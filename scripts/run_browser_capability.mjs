#!/usr/bin/env node
import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { lstat, mkdir, mkdtemp, readFile, realpath, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import process from 'node:process';

import { mergeMotionEvidence } from './browser_motion_evidence.mjs';
import { removeBrowserProfileBestEffort } from './browser_profile_cleanup.mjs';
import { waitForWebSocketOpen } from './browser_websocket_ready.mjs';

class BrowserContractError extends Error {}
class BrowserBlockedError extends Error {}

const NETWORK_OBSERVATION_MS = 1300;
const MOTION_LIMIT_MS = 50;
const MOTION_OBSERVATION_POINTS_MS = [0, 50, 150, 300, 600, 1000, 1250];
const REQUIRED_NO_NETWORK_DIRECTIVES = new Map([
  ['default-src', ["'none'"]],
  ['base-uri', ["'none'"]],
  ['connect-src', ["'none'"]],
  ['form-action', ["'none'"]],
  ['frame-src', ["'none'"]],
  ['img-src', ['data:']],
  ['media-src', ['data:']],
  ['object-src', ["'none'"]],
  ['script-src', ["'unsafe-inline'"]],
  ['style-src', ["'unsafe-inline'"]],
]);
const ALLOWED_EXTRA_NO_NETWORK_DIRECTIVES = new Map([
  ['child-src', ["'none'"]],
  ['font-src', ["'none'"]],
  ['manifest-src', ["'none'"]],
  ['navigate-to', ["'none'"]],
  ['prefetch-src', ["'none'"]],
  ['worker-src', ["'none'"]],
]);

function contentSecurityPolicyDirectives(content) {
  const directives = new Map();
  for (const rawDirective of String(content || '').split(';')) {
    const parts = rawDirective.trim().split(/\s+/).filter(Boolean);
    if (!parts.length) continue;
    const name = parts[0].toLowerCase();
    if (directives.has(name)) return null;
    directives.set(name, parts.slice(1).map((value) => value.toLowerCase()));
  }
  return directives;
}

function sameDirectiveValues(actual, expected) {
  return Array.isArray(actual)
    && actual.length === expected.length
    && actual.every((value, index) => value === expected[index]);
}

function hasDurableNoNetworkPolicy(content) {
  const directives = contentSecurityPolicyDirectives(content);
  if (!directives) return false;
  for (const [name, expected] of REQUIRED_NO_NETWORK_DIRECTIVES) {
    if (!sameDirectiveValues(directives.get(name), expected)) return false;
  }
  const allowedNames = new Set([
    ...REQUIRED_NO_NETWORK_DIRECTIVES.keys(),
    ...ALLOWED_EXTRA_NO_NETWORK_DIRECTIVES.keys(),
  ]);
  for (const [name, values] of directives) {
    if (!allowedNames.has(name)) return false;
    const expected = ALLOWED_EXTRA_NO_NETWORK_DIRECTIVES.get(name);
    if (expected && !sameDirectiveValues(values, expected)) return false;
  }
  return true;
}

function pixels(value) {
  const parsed = Number.parseFloat(String(value || '0'));
  return Number.isFinite(parsed) ? parsed : 0;
}

function colorHasVisibleAlpha(value) {
  const text = String(value || '').trim().toLowerCase();
  if (!text || text === 'transparent') return false;
  const rgba = text.match(/^rgba\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\)$/);
  return !rgba || Number(rgba[1]) > 0.01;
}

function shadowIsVisible(value) {
  const text = String(value || '').trim().toLowerCase();
  if (!text || text === 'none') return false;
  const alphaValues = [...text.matchAll(/rgba\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\)/g)]
    .map((match) => Number(match[1]));
  return !alphaValues.length || alphaValues.some((alpha) => alpha > 0.01);
}

function filterHasRenderedEffect(value) {
  let text = String(value || '').trim().toLowerCase();
  if (!text || text === 'none') return false;
  const neutralFilters = [
    /brightness\((?:1(?:\.0+)?|100(?:\.0+)?%)\)/g,
    /contrast\((?:1(?:\.0+)?|100(?:\.0+)?%)\)/g,
    /opacity\((?:1(?:\.0+)?|100(?:\.0+)?%)\)/g,
    /saturate\((?:1(?:\.0+)?|100(?:\.0+)?%)\)/g,
    /blur\(0(?:\.0+)?(?:px|em|rem|vh|vw|vmin|vmax|cm|mm|in|pt|pc)?\)/g,
    /grayscale\((?:0(?:\.0+)?|0(?:\.0+)?%)\)/g,
    /invert\((?:0(?:\.0+)?|0(?:\.0+)?%)\)/g,
    /sepia\((?:0(?:\.0+)?|0(?:\.0+)?%)\)/g,
    /hue-rotate\(0(?:\.0+)?(?:deg|grad|rad|turn)\)/g,
  ];
  for (const neutral of neutralFilters) text = text.replace(neutral, '');
  return text.replace(/\s+/g, '').length > 0;
}

function focusStyleRenderedChange(before, after) {
  if (!before || !after) return false;
  const outlineChanged = [
    'outlineStyle',
    'outlineWidth',
    'outlineColor',
    'outlineOffset',
  ].some((key) => before[key] !== after[key]);
  const outlineVisible = outlineChanged
    && !['none', 'hidden'].includes(String(after.outlineStyle || '').toLowerCase())
    && pixels(after.outlineWidth) > 0
    && colorHasVisibleAlpha(after.outlineColor);

  const shadowVisible = before.boxShadow !== after.boxShadow
    && shadowIsVisible(after.boxShadow);
  const borderVisible = [
    'borderStyle',
    'borderWidth',
    'borderColor',
  ].some((key) => before[key] !== after[key])
    && !['none', 'hidden'].includes(String(after.borderStyle || '').toLowerCase())
    && pixels(after.borderWidth) > 0
    && colorHasVisibleAlpha(after.borderColor);
  const backgroundVisible = before.backgroundColor !== after.backgroundColor
    && colorHasVisibleAlpha(after.backgroundColor);
  const foregroundVisible = before.color !== after.color
    && colorHasVisibleAlpha(after.color);
  const filterVisible = before.filter !== after.filter
    && filterHasRenderedEffect(after.filter);

  return Boolean(
    outlineVisible
    || shadowVisible
    || borderVisible
    || backgroundVisible
    || foregroundVisible
    || filterVisible
  );
}

function focusSignatureRenderedChange(before, after) {
  if (!Array.isArray(before) || !Array.isArray(after)) return false;
  const count = Math.min(before.length, after.length);
  for (let index = 0; index < count; index += 1) {
    const beforeEntry = before[index];
    const afterEntry = after[index];
    if (!beforeEntry || !afterEntry || beforeEntry.role !== afterEntry.role) continue;
    if (focusStyleRenderedChange(beforeEntry.style, afterEntry.style)) return true;
    for (const pseudo of ['before', 'after']) {
      if (focusStyleRenderedChange(beforeEntry[pseudo], afterEntry[pseudo])) return true;
    }
  }
  return false;
}

const ACCESSIBLE_NAME_SOURCE = `(element) => {
  if (!(element instanceof HTMLElement)) return '';
  const labelledBy = String(element.getAttribute('aria-labelledby') || '')
    .split(/\s+/)
    .filter(Boolean)
    .map((id) => document.getElementById(id)?.textContent?.trim() || '')
    .filter(Boolean)
    .join(' ')
    .trim();
  if (labelledBy) return labelledBy;
  const ariaLabel = String(element.getAttribute('aria-label') || '').trim();
  if (ariaLabel) return ariaLabel;
  return [...(element.labels || [])]
    .map((label) => label.textContent?.trim() || '')
    .filter(Boolean)
    .join(' ')
    .trim();
}`;

function keyDescriptor(character) {
  const upper = character.toUpperCase();
  const letter = /^[A-Z]$/.test(upper);
  const digit = /^\d$/.test(character);
  return {
    key: character,
    code: letter ? `Key${upper}` : digit ? `Digit${character}` : character,
    windowsVirtualKeyCode: upper.codePointAt(0),
    nativeVirtualKeyCode: upper.codePointAt(0),
  };
}

async function typeWithKeyboard(client, text) {
  for (const character of text) {
    const descriptor = keyDescriptor(character);
    await client.send('Input.dispatchKeyEvent', {
      type: 'keyDown',
      ...descriptor,
      text: character,
      unmodifiedText: character,
    });
    await client.send('Input.dispatchKeyEvent', {
      type: 'keyUp',
      ...descriptor,
    });
  }
}

function parseArgs(argv) {
  const args = { root: null, outputDir: null, entrypoint: 'index.html', width: 390, height: 844, forbiddenText: null };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (key === '--root') args.root = value;
    else if (key === '--output-dir') args.outputDir = value;
    else if (key === '--entrypoint') args.entrypoint = value;
    else if (key === '--width') args.width = Number(value);
    else if (key === '--height') args.height = Number(value);
    else if (key === '--forbidden-text') args.forbiddenText = value;
    else throw new BrowserContractError(`unknown or incomplete argument: ${key}`);
    index += 1;
  }
  if (!args.root || !args.outputDir) throw new BrowserContractError('--root and --output-dir are required');
  if (!Number.isInteger(args.width) || args.width < 240 || !Number.isInteger(args.height) || args.height < 320) {
    throw new BrowserContractError('viewport width and height must be sensible integers');
  }
  return args;
}

function safePath(root, value) {
  if (!value || isAbsolute(value) || value.includes('\\') || value.split('/').some((part) => part === '..')) {
    throw new BrowserContractError('entrypoint must be a safe relative path');
  }
  const candidate = resolve(root, value);
  const rel = relative(resolve(root), candidate);
  if (rel === '..' || rel.startsWith(`..${sep}`) || isAbsolute(rel)) {
    throw new BrowserContractError('entrypoint escapes the served root');
  }
  return candidate;
}

async function requireRegularFileInsideRoot(root, candidate) {
  const info = await lstat(candidate);
  if (info.isSymbolicLink()) throw new BrowserContractError('entrypoint must not be a symlink');
  if (!info.isFile()) throw new BrowserContractError('entrypoint is not a file');
  const [realRoot, realCandidate] = await Promise.all([realpath(root), realpath(candidate)]);
  const rel = relative(realRoot, realCandidate);
  if (rel === '..' || rel.startsWith(`..${sep}`) || isAbsolute(rel)) {
    throw new BrowserContractError('entrypoint resolves outside the served root');
  }
}

function findChrome() {
  if (process.env.CHROME_PATH) {
    if (!existsSync(process.env.CHROME_PATH)) {
      throw new BrowserBlockedError(`Chrome executable does not exist: ${process.env.CHROME_PATH}`);
    }
    return process.env.CHROME_PATH;
  }
  for (const candidate of ['google-chrome-stable', 'google-chrome', 'chromium', 'chromium-browser']) {
    const found = spawnSync('sh', ['-lc', `command -v ${candidate}`], { encoding: 'utf8' });
    if (found.status === 0 && found.stdout.trim()) return found.stdout.trim();
  }
  throw new BrowserBlockedError('Chrome or Chromium is not installed');
}

async function waitForDevTools(userDataDir, chrome, timeoutMs = 15000) {
  const activePort = join(userDataDir, 'DevToolsActivePort');
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (chrome.__designStudioSpawnError) {
      throw new BrowserBlockedError(`Chrome could not start: ${chrome.__designStudioSpawnError.message || String(chrome.__designStudioSpawnError)}`);
    }
    if (chrome.exitCode !== null) throw new BrowserBlockedError(`Chrome exited before DevTools was ready (status ${chrome.exitCode})`);
    try {
      const [portLine] = (await readFile(activePort, 'utf8')).trim().split(/\r?\n/);
      const port = Number(portLine);
      if (Number.isInteger(port) && port > 0) return port;
    } catch (error) {
      if (error?.code !== 'ENOENT') throw error;
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
  }
  throw new BrowserBlockedError('Chrome DevTools did not become ready');
}

async function getPageTarget(port, timeoutMs = 10000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`);
      if (response.ok) {
        const targets = await response.json();
        const page = targets.find((target) => target.type === 'page' && target.webSocketDebuggerUrl);
        if (page) return page;
      }
    } catch {
      // Retry while Chrome starts.
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
  }
  throw new BrowserBlockedError('Chrome exposed no debuggable page target');
}

class CdpClient {
  constructor(url) {
    this.url = url;
    this.socket = null;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
  }

  async connect() {
    this.socket = new WebSocket(this.url);
    await waitForWebSocketOpen(this.socket, {
      timeoutMs: 10_000,
      errorFactory: (message) => new BrowserBlockedError(message),
    });
    this.socket.addEventListener('message', (event) => {
      const message = JSON.parse(String(event.data));
      if (message.method) {
        for (const listener of this.listeners.get(message.method) || []) {
          listener(message.params || {}, message.sessionId || null);
        }
      }
      if (!message.id) return;
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      clearTimeout(pending.timer);
      if (message.error) pending.reject(new BrowserContractError(`${pending.method}: ${message.error.message}`));
      else pending.resolve(message.result || {});
    });
    this.socket.addEventListener('close', () => {
      for (const pending of this.pending.values()) {
        clearTimeout(pending.timer);
        pending.reject(new BrowserBlockedError('DevTools websocket closed unexpectedly'));
      }
      this.pending.clear();
    });
  }

  on(method, listener) {
    const listeners = this.listeners.get(method) || [];
    listeners.push(listener);
    this.listeners.set(method, listeners);
  }

  send(method, params = {}, sessionId = null) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return Promise.reject(new BrowserBlockedError('DevTools websocket is not open'));
    }
    const id = this.nextId;
    this.nextId += 1;
    return new Promise((resolvePromise, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new BrowserBlockedError(`DevTools command timed out: ${method}`));
      }, 10000);
      this.pending.set(id, { method, resolve: resolvePromise, reject, timer });
      const message = { id, method, params };
      if (sessionId) message.sessionId = sessionId;
      this.socket.send(JSON.stringify(message));
    });
  }

  close() {
    if (this.socket && this.socket.readyState <= WebSocket.OPEN) this.socket.close();
  }
}

async function evaluate(client, expression) {
  const result = await client.send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true,
  });
  if (result.exceptionDetails) throw new BrowserContractError('page evaluation raised an exception');
  return result.result?.value;
}

async function dispatchKey(client, key, code, virtualKeyCode, modifiers = 0) {
  const params = {
    key,
    code,
    windowsVirtualKeyCode: virtualKeyCode,
    nativeVirtualKeyCode: virtualKeyCode,
    modifiers,
  };
  const text = key === 'Enter' ? '\r' : key === ' ' ? ' ' : null;
  await client.send('Input.dispatchKeyEvent', {
    type: 'keyDown',
    ...params,
    ...(text === null ? {} : { text, unmodifiedText: text }),
  });
  await client.send('Input.dispatchKeyEvent', { type: 'keyUp', ...params });
}

async function tabUntil(client, expression, { reverse = false, attempts = 20 } = {}) {
  for (let index = 0; index <= attempts; index += 1) {
    if (await evaluate(client, expression)) return true;
    await dispatchKey(client, 'Tab', 'Tab', 9, reverse ? 8 : 0);
  }
  return false;
}

async function measureMotion(client) {
  return evaluate(client, `(() => {
    const parseTimes = (value) => String(value || '').split(',').map((part) => {
      const text = part.trim();
      if (text.endsWith('ms')) return Number.parseFloat(text) || 0;
      if (text.endsWith('s')) return (Number.parseFloat(text) || 0) * 1000;
      return 0;
    });
    const pairedMaximum = (durations, delays) => {
      if (!durations.length) return 0;
      const safeDelays = delays.length ? delays : [0];
      const count = Math.max(durations.length, safeDelays.length);
      let maximum = 0;
      for (let index = 0; index < count; index += 1) {
        maximum = Math.max(
          maximum,
          durations[index % durations.length] + Math.max(0, safeDelays[index % safeDelays.length]),
        );
      }
      return maximum;
    };
    let maxMs = 0;
    let activeElementCount = 0;
    const samples = [];
    for (const element of document.querySelectorAll('*')) {
      const style = getComputedStyle(element);
      const transitionMs = pairedMaximum(
        parseTimes(style.transitionDuration),
        parseTimes(style.transitionDelay),
      );
      const animationMs = pairedMaximum(
        parseTimes(style.animationDuration),
        parseTimes(style.animationDelay),
      );
      const elementMaxMs = Math.max(transitionMs, animationMs);
      if (elementMaxMs > 1) {
        activeElementCount += 1;
        maxMs = Math.max(maxMs, elementMaxMs);
        if (samples.length < 8) {
          samples.push({ source: 'computed-style', tag: element.tagName.toLowerCase(), id: element.id || null, maxMs: elementMaxMs });
        }
      }
    }
    try {
      for (const animation of document.getAnimations({ subtree: true })) {
        if (!['running', 'pending'].includes(animation.playState) || animation.playbackRate === 0) continue;
        const timing = animation.effect?.getComputedTiming?.() || {};
        const endTime = Number(timing.endTime);
        const animationMaxMs = Number.isFinite(endTime) && endTime >= 0
          ? endTime
          : 60_000;
        if (animationMaxMs <= 1) continue;
        activeElementCount += 1;
        maxMs = Math.max(maxMs, animationMaxMs);
        if (samples.length < 8) {
          const target = animation.effect?.target;
          samples.push({
            source: 'web-animation',
            tag: target?.tagName?.toLowerCase?.() || null,
            id: target?.id || null,
            pseudoElement: animation.effect?.pseudoElement || null,
            maxMs: animationMaxMs,
          });
        }
      }
    } catch {
      // Older Chromium builds may not expose subtree animation enumeration.
    }
    return {
      prefersReducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
      maxMs,
      activeElementCount,
      samples,
    };
  })()`);
}

async function sampleMotionWindow(client) {
  const evidence = [];
  let elapsedMs = 0;
  for (const pointMs of MOTION_OBSERVATION_POINTS_MS) {
    const delayMs = Math.max(0, pointMs - elapsedMs);
    if (delayMs) await new Promise((resolvePromise) => setTimeout(resolvePromise, delayMs));
    evidence.push({
      ...(await measureMotion(client)),
      observedAtMs: pointMs,
    });
    elapsedMs = pointMs;
  }
  return {
    ...mergeMotionEvidence(evidence),
    observedForMs: elapsedMs,
  };
}

function motionPairSupported(normal, reduced) {
  return Boolean(
    reduced?.prefersReducedMotion
    && reduced.maxMs <= MOTION_LIMIT_MS
    && reduced.maxMs <= normal.maxMs + 1
    && reduced.activeElementCount <= normal.activeElementCount
  );
}

function isExternalNetworkUrl(value) {
  try {
    return ['http:', 'https:', 'ws:', 'wss:', 'ftp:'].includes(new URL(value).protocol);
  } catch {
    return true;
  }
}

function trackPromise(set, promise) {
  set.add(promise);
  promise.finally(() => set.delete(promise)).catch(() => {});
}

async function stopChrome(chrome) {
  if (chrome.exitCode !== null) return;
  const exited = new Promise((resolvePromise) => chrome.once('exit', resolvePromise));
  chrome.kill('SIGTERM');
  await Promise.race([
    exited,
    new Promise((resolvePromise) => setTimeout(resolvePromise, 500)),
  ]);
  if (chrome.exitCode === null) chrome.kill('SIGKILL');
  await Promise.race([
    exited,
    new Promise((resolvePromise) => setTimeout(resolvePromise, 1000)),
  ]);
}

const POPUP_GUARD_SOURCE = `(() => {
  if (window.__designStudioPopupGuardInstalled) return true;
  const attempts = [];
  const networkAttempts = [];
  const record = (value) => attempts.push(String(value ?? 'about:blank'));
  const recordNetwork = (value) => networkAttempts.push(String(value ?? 'about:blank'));
  Object.defineProperty(window, '__designStudioPopupAttempts', {
    configurable: false,
    enumerable: false,
    get: () => attempts.slice(),
  });
  Object.defineProperty(window, '__designStudioNetworkAttempts', {
    configurable: false,
    enumerable: false,
    get: () => networkAttempts.slice(),
  });
  Object.defineProperty(window, '__designStudioPopupGuardInstalled', {
    configurable: false,
    enumerable: false,
    value: true,
  });
  const blockedNetworkError = () => new DOMException(
    'External network access is blocked by the Design Studio capability probe',
    'SecurityError',
  );
  const BlockedWebSocket = function (url) {
    recordNetwork(url);
    throw blockedNetworkError();
  };
  for (const [name, value] of Object.entries({ CONNECTING: 0, OPEN: 1, CLOSING: 2, CLOSED: 3 })) {
    Object.defineProperty(BlockedWebSocket, name, { value, enumerable: true });
    Object.defineProperty(BlockedWebSocket.prototype, name, { value, enumerable: true });
  }
  Object.defineProperty(window, 'WebSocket', { configurable: false, value: BlockedWebSocket });
  if ('EventSource' in window) {
    Object.defineProperty(window, 'EventSource', {
      configurable: false,
      value: function BlockedEventSource(url) {
        recordNetwork(url);
        throw blockedNetworkError();
      },
    });
  }
  if ('XMLHttpRequest' in window) {
    Object.defineProperty(window, 'XMLHttpRequest', {
      configurable: false,
      value: function BlockedXMLHttpRequest() {
        recordNetwork('XMLHttpRequest');
        throw blockedNetworkError();
      },
    });
  }
  window.fetch = (input) => {
    recordNetwork(input instanceof Request ? input.url : input);
    return Promise.reject(blockedNetworkError());
  };
  if (navigator && typeof navigator.sendBeacon === 'function') {
    Object.defineProperty(navigator, 'sendBeacon', {
      configurable: false,
      value: (url) => {
        recordNetwork(url);
        return false;
      },
    });
  }
  window.open = (url) => {
    record(url);
    return null;
  };
  const anchorClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function (...args) {
    if (String(this.target || '').toLowerCase() === '_blank') {
      record(this.href || this.getAttribute('href'));
      return undefined;
    }
    return anchorClick.apply(this, args);
  };
  const formSubmit = HTMLFormElement.prototype.submit;
  HTMLFormElement.prototype.submit = function (...args) {
    if (String(this.target || '').toLowerCase() === '_blank') {
      record(this.action || this.getAttribute('action'));
      return undefined;
    }
    return formSubmit.apply(this, args);
  };
  document.addEventListener('click', (event) => {
    const anchor = event.target instanceof Element
      ? event.target.closest('a[target="_blank"], a[target="_BLANK"]')
      : null;
    if (!anchor) return;
    record(anchor.href || anchor.getAttribute('href'));
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);
  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (String(form.target || '').toLowerCase() !== '_blank') return;
    record(form.action || form.getAttribute('action'));
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);
  return true;
})()`;

const ELEMENT_RENDERED_SOURCE = `(element) => {
  if (!element) return false;
  const rect = element.getBoundingClientRect();
  if (
    rect.width <= 0
    || rect.height <= 0
    || rect.bottom <= 0
    || rect.right <= 0
    || rect.top >= window.innerHeight
    || rect.left >= window.innerWidth
  ) return false;

  let left = Math.max(0, rect.left);
  let top = Math.max(0, rect.top);
  let right = Math.min(window.innerWidth, rect.right);
  let bottom = Math.min(window.innerHeight, rect.bottom);
  let effectiveOpacity = 1;
  for (let current = element; current; current = current.parentElement) {
    const style = getComputedStyle(current);
    effectiveOpacity *= Number.parseFloat(style.opacity || '1');
    if (
      current.hidden
      || style.display === 'none'
      || style.visibility === 'hidden'
      || style.visibility === 'collapse'
      || effectiveOpacity <= 0.01
    ) return false;

    if (current !== element) {
      const clips = [style.overflow, style.overflowX, style.overflowY]
        .some((value) => ['hidden', 'clip', 'auto', 'scroll'].includes(value));
      if (clips) {
        const ancestorRect = current.getBoundingClientRect();
        left = Math.max(left, ancestorRect.left);
        top = Math.max(top, ancestorRect.top);
        right = Math.min(right, ancestorRect.right);
        bottom = Math.min(bottom, ancestorRect.bottom);
        if (right <= left || bottom <= top) return false;
      }
    }
  }
  return right > left && bottom > top;
}`;

const PSEUDO_TEXT_SOURCE = `(element) => {
  if (!(element instanceof Element)) return '';
  return ['::before', '::after']
    .map((pseudo) => {
      const style = getComputedStyle(element, pseudo);
      const raw = String(style.content || '').trim();
      const normalizedRaw = raw.toLowerCase();
      if (
        !raw
        || normalizedRaw === 'none'
        || normalizedRaw === 'normal'
        || style.display === 'none'
        || style.visibility === 'hidden'
        || Number.parseFloat(style.opacity || '1') <= 0.01
      ) return '';
      const quoted = raw.match(/^(['"])(.*)\\1$/);
      return quoted ? quoted[2] : raw;
    })
    .filter(Boolean)
    .join(' ')
    .trim();
}`;


const FOCUS_SIGNATURE_SOURCE = `(element) => {
  const styleSnapshot = (node, pseudo = null) => {
    if (!node) return null;
    const style = getComputedStyle(node, pseudo);
    if (pseudo && ['none', 'normal', ''].includes(String(style.content || '').replace(/^['"]|['"]$/g, ''))) {
      return null;
    }
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: style.outlineWidth,
      outlineColor: style.outlineColor,
      outlineOffset: style.outlineOffset,
      boxShadow: style.boxShadow,
      borderColor: style.borderColor,
      borderWidth: style.borderWidth,
      borderStyle: style.borderStyle,
      backgroundColor: style.backgroundColor,
      color: style.color,
      filter: style.filter,
    };
  };
  const entries = [];
  let current = element;
  let depth = 0;
  while (current && depth < 8) {
    entries.push({
      role: depth === 0 ? 'target' : 'ancestor-' + depth,
      style: styleSnapshot(current),
      before: styleSnapshot(current, '::before'),
      after: styleSnapshot(current, '::after'),
    });
    if (current === document.body) break;
    current = current.parentElement;
    depth += 1;
  }
  return entries;
}`;

const SUBMISSION_TRACE_SOURCE = `(() => {
  if (window.__designStudioSubmissionTraceInstalled) return true;
  const trace = {
    trustedKeydown: false,
    trustedSubmit: false,
    causedSuccess: false,
    successObserved: false,
    keydownAt: null,
    submitAt: null,
  };
  const success = () => document.querySelector('#capability-success');
  const rendered = ${ELEMENT_RENDERED_SOURCE};
  const pseudoText = ${PSEUDO_TEXT_SOURCE};
  const snapshot = () => {
    const element = success();
    return {
      text: element?.textContent?.trim() || '',
      pseudoText: pseudoText(element),
      hidden: Boolean(element?.hidden),
      className: element?.className || '',
      style: element?.getAttribute?.('style') || '',
      ariaHidden: element?.getAttribute?.('aria-hidden') || '',
    };
  };
  const nativeSetTimeout = window.setTimeout.bind(window);
  const nativeQueueMicrotask = window.queueMicrotask.bind(window);
  const submissionSnapshots = new Map();
  let submissionSequence = 0;
  let activeSubmissionId = null;
  const markSuccessTransition = (submissionId, beforeOverride = null) => {
    const before = beforeOverride || submissionSnapshots.get(submissionId);
    if (!before) return;
    const after = snapshot();
    if (
      JSON.stringify(before) !== JSON.stringify(after)
      && after.text === 'Capability complete'
    ) {
      trace.causedSuccess = true;
      submissionSnapshots.delete(submissionId);
    }
  };
  window.setTimeout = function tracedSetTimeout(callback, delay, ...args) {
    if (typeof callback !== 'function' || activeSubmissionId === null) {
      return nativeSetTimeout(callback, delay, ...args);
    }
    const submissionId = activeSubmissionId;
    return nativeSetTimeout(function tracedTimeoutCallback(...callbackArgs) {
      const beforeCallback = snapshot();
      const previousSubmissionId = activeSubmissionId;
      activeSubmissionId = submissionId;
      try {
        return callback.apply(this, callbackArgs);
      } finally {
        activeSubmissionId = previousSubmissionId;
        nativeQueueMicrotask(() => markSuccessTransition(
          submissionId,
          beforeCallback,
        ));
      }
    }, delay, ...args);
  };
  const observer = new MutationObserver(() => {
    const element = success();
    if (rendered(element) && element.textContent.trim().length > 0) {
      trace.successObserved = true;
    }
  });
  if (document.documentElement) {
    observer.observe(document.documentElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['hidden', 'class', 'style', 'aria-hidden'],
    });
  }
  document.addEventListener('keydown', (event) => {
    const form = document.querySelector('#capability-form');
    const submit = form?.querySelector('button[type="submit"], input[type="submit"]');
    if (
      event.isTrusted
      && event.target === submit
      && ['Enter', ' '].includes(event.key)
    ) {
      trace.trustedKeydown = true;
      trace.keydownAt = performance.now();
    }
  }, true);
  document.addEventListener('submit', (event) => {
    const form = document.querySelector('#capability-form');
    const recentKeyboardActivation = trace.trustedKeydown
      && Number.isFinite(trace.keydownAt)
      && performance.now() - trace.keydownAt < 1000;
    if (event.target !== form || !event.isTrusted || !recentKeyboardActivation) return;
    submissionSequence += 1;
    const submissionId = submissionSequence;
    trace.trustedSubmit = true;
    trace.submitAt = performance.now();
    submissionSnapshots.set(submissionId, snapshot());
    activeSubmissionId = submissionId;
    nativeSetTimeout(() => {
      markSuccessTransition(submissionId);
      if (activeSubmissionId === submissionId) activeSubmissionId = null;
    }, 0);
  }, true);
  Object.defineProperty(window, '__designStudioSubmissionTrace', {
    configurable: false,
    enumerable: false,
    get: () => ({ ...trace }),
  });
  Object.defineProperty(window, '__designStudioSubmissionTraceInstalled', {
    configurable: false,
    enumerable: false,
    value: true,
  });
  return true;
})()`;

async function replaySubmissionWithReducedMotion(client, frameId, html) {
  const fallback = {
    performed: false,
    inputKeyboardReachable: false,
    submitKeyboardReachable: false,
    prefersReducedMotion: false,
    maxMs: 0,
    activeElementCount: 0,
    samples: [],
    observedForMs: 0,
    contractPassed: false,
    error: null,
  };
  try {
    await client.send('Emulation.setEmulatedMedia', {
      features: [{ name: 'prefers-reduced-motion', value: 'reduce' }],
    });
    await evaluate(client, `document.documentElement?.setAttribute('data-design-studio-replay-stale', 'true')`);
    await client.send('Page.navigate', { url: 'about:blank' });
    await client.send('Page.setDocumentContent', { frameId, html });
    const replayReadyDeadline = Date.now() + 5000;
    let replayReady = false;
    while (Date.now() < replayReadyDeadline) {
      try {
        replayReady = Boolean(await evaluate(client, `Boolean(
          document.readyState === 'complete'
          && !document.documentElement?.hasAttribute('data-design-studio-replay-stale')
          && document.querySelector('#capability-form')
          && document.querySelector('#capability-name')
        )`));
      } catch {
        replayReady = false;
      }
      if (replayReady) break;
      await new Promise((resolvePromise) => setTimeout(resolvePromise, 25));
    }
    if (!replayReady) throw new BrowserContractError('reduced-motion replay document did not become ready');
    await evaluate(client, POPUP_GUARD_SOURCE);
    if (await evaluate(client, `Boolean(document.activeElement instanceof HTMLElement)`)) {
      await evaluate(client, `document.activeElement.blur()`);
    }
    const inputKeyboardReachable = await tabUntil(
      client,
      `document.activeElement === document.querySelector('#capability-name')`,
    );
    if (inputKeyboardReachable) await typeWithKeyboard(client, 'Ada');
    const submitKeyboardReachable = await tabUntil(
      client,
      `(() => { const form = document.querySelector('#capability-form'); const submit = form?.querySelector('button[type="submit"], input[type="submit"]'); return document.activeElement === submit; })()`,
    );
    if (submitKeyboardReachable) await dispatchKey(client, 'Enter', 'Enter', 13);
    const motion = await sampleMotionWindow(client);
    const remainingObservationMs = Math.max(
      0,
      NETWORK_OBSERVATION_MS - motion.observedForMs,
    );
    if (remainingObservationMs) {
      await new Promise((resolvePromise) => setTimeout(resolvePromise, remainingObservationMs));
    }
    const replayState = await evaluate(client, `(() => {
      const form = document.querySelector('#capability-form');
      const input = document.querySelector('#capability-name');
      const success = document.querySelector('#capability-success');
      const submit = form?.querySelector('button[type="submit"], input[type="submit"]');
      const label = document.querySelector('label[for="capability-name"]');
      const rendered = ${ELEMENT_RENDERED_SOURCE};
      const pseudoText = ${PSEUDO_TEXT_SOURCE};
      return {
        successVisible: rendered(success),
        successText: success?.textContent?.trim() || '',
        successPseudoText: pseudoText(success),
        inputValue: input?.value || '',
        formVisibleAfter: [form, label, input, submit].every(rendered),
        url: location.href,
        activeElementTag: document.activeElement?.tagName?.toLowerCase?.() || null,
        activeElementType: document.activeElement?.getAttribute?.('type') || null,
      };
    })()`);
    const contractPassed = Boolean(
      inputKeyboardReachable
      && submitKeyboardReachable
      && replayState.successVisible
      && replayState.successText === 'Capability complete'
      && !replayState.successPseudoText
      && replayState.inputValue === 'Ada'
      && replayState.formVisibleAfter
      && replayState.url === 'about:blank'
    );
    return {
      ...motion,
      performed: Boolean(inputKeyboardReachable && submitKeyboardReachable),
      contractPassed,
      inputKeyboardReachable,
      submitKeyboardReachable,
      replayState,
      error: null,
    };
  } catch (error) {
    return {
      ...fallback,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function runBrowserProbe({ root, outputDir, entrypoint, width, height, forbiddenText }) {
  const resolvedRoot = resolve(root);
  const resolvedOutput = resolve(outputDir);
  const entryPath = safePath(resolvedRoot, entrypoint);
  await requireRegularFileInsideRoot(resolvedRoot, entryPath);
  const html = await readFile(entryPath, 'utf8');
  await mkdir(resolvedOutput, { recursive: true });

  const chromePath = findChrome();
  const userDataDir = await mkdtemp(join(tmpdir(), 'design-studio-browser-'));
  let chrome = null;
  let stderr = '';
  let client;
  try {
    chrome = spawn(chromePath, [
      '--headless=new',
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-background-networking',
      '--disable-component-update',
      '--proxy-server=http://127.0.0.1:9',
      '--hide-scrollbars',
      '--remote-debugging-port=0',
      `--user-data-dir=${userDataDir}`,
      `--window-size=${width},${height}`,
      'about:blank',
    ], { stdio: ['ignore', 'ignore', 'pipe'] });
    chrome.__designStudioSpawnError = null;
    chrome.once('error', (error) => { chrome.__designStudioSpawnError = error; });
    if (chrome.stderr) {
      chrome.stderr.setEncoding('utf8');
      chrome.stderr.on('data', (chunk) => { stderr += chunk; });
    }

    const devToolsPort = await waitForDevTools(userDataDir, chrome);
    const target = await getPageTarget(devToolsPort);
    client = new CdpClient(target.webSocketDebuggerUrl);
    await client.connect();

    const requestUrls = new Set();
    const externalRequestUrls = new Set();
    const blockedRequestUrls = new Set();
    const blockedPopupTargets = new Set();
    const blockedAuxiliaryTargets = new Set();
    const requestById = new Map();
    const interceptionPromises = new Set();

    const recordExternal = (url, blocked = false) => {
      if (typeof url !== 'string' || !url || !isExternalNetworkUrl(url)) return;
      requestUrls.add(url);
      externalRequestUrls.add(url);
      if (blocked) blockedRequestUrls.add(url);
    };

    client.on('Network.requestWillBeSent', (params, sessionId) => {
      const url = params?.request?.url;
      if (typeof url !== 'string' || !url) return;
      requestUrls.add(url);
      if (params.requestId) requestById.set(`${sessionId || 'main'}:${params.requestId}`, url);
      if (isExternalNetworkUrl(url)) externalRequestUrls.add(url);
    });
    client.on('Network.loadingFailed', (params, sessionId) => {
      const url = requestById.get(`${sessionId || 'main'}:${params.requestId}`);
      if (url && isExternalNetworkUrl(url) && (params.blockedReason || params.errorText === 'net::ERR_BLOCKED_BY_CLIENT')) {
        blockedRequestUrls.add(url);
      }
    });
    client.on('Network.webSocketCreated', (params) => {
      const url = params?.url;
      if (typeof url === 'string' && isExternalNetworkUrl(url)) recordExternal(url, true);
    });
    client.on('Fetch.requestPaused', (params, sessionId) => {
      const url = params?.request?.url;
      if (typeof url === 'string' && isExternalNetworkUrl(url)) {
        recordExternal(url, true);
        trackPromise(
          interceptionPromises,
          client.send('Fetch.failRequest', { requestId: params.requestId, errorReason: 'BlockedByClient' }, sessionId).catch(() => {}),
        );
      } else {
        trackPromise(
          interceptionPromises,
          client.send('Fetch.continueRequest', { requestId: params.requestId }, sessionId).catch(() => {}),
        );
      }
    });

    const containTarget = (info) => {
      if (!info || !info.targetId || info.targetId === target.id) return;
      const containedTypes = new Set(['page', 'worker', 'shared_worker', 'service_worker']);
      if (!containedTypes.has(info.type)) return;
      if (typeof info.url === 'string' && info.url) recordExternal(info.url, true);
      if (info.type === 'page') blockedPopupTargets.add(info.targetId);
      else blockedAuxiliaryTargets.add(info.targetId);
      const close = Promise.race([
        client.send('Target.closeTarget', { targetId: info.targetId }).catch(() => {}),
        new Promise((resolvePromise) => setTimeout(resolvePromise, 500)),
      ]);
      trackPromise(interceptionPromises, close);
    };
    client.on('Target.targetCreated', (params) => containTarget(params?.targetInfo));
    client.on('Target.targetInfoChanged', (params) => containTarget(params?.targetInfo));
    client.on('Target.attachedToTarget', (params, sessionId) => {
      containTarget(params?.targetInfo);
      if (params?.waitingForDebugger) {
        trackPromise(
          interceptionPromises,
          client.send('Runtime.runIfWaitingForDebugger', {}, params.sessionId || sessionId).catch(() => {}),
        );
      }
    });

    await client.send('Page.enable');
    await client.send('Runtime.enable');
    await client.send('Network.enable');
    await client.send('Fetch.enable', { patterns: [{ urlPattern: '*', requestStage: 'Request' }] });
    await client.send('Network.setBlockedURLs', { urls: ['ws://*', 'wss://*', 'ftp://*'] });
    await client.send('Target.setDiscoverTargets', { discover: true });
    await client.send('Target.setAutoAttach', { autoAttach: true, waitForDebuggerOnStart: true, flatten: true });
    await client.send('Page.addScriptToEvaluateOnNewDocument', { source: POPUP_GUARD_SOURCE });
    await evaluate(client, POPUP_GUARD_SOURCE);
    await client.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
    await client.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
    const frameTree = await client.send('Page.getFrameTree');
    const frameId = frameTree.frameTree?.frame?.id;
    if (!frameId) throw new BrowserBlockedError('Chrome exposed no main frame');
    await client.send('Page.setDocumentContent', { frameId, html });
    await evaluate(client, POPUP_GUARD_SOURCE);
    await evaluate(client, SUBMISSION_TRACE_SOURCE);

    const normalMotion = await measureMotion(client);
    await client.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    const reducedMotion = await measureMotion(client);
    await client.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });

    const initial = await evaluate(client, `(() => {
      const form = document.querySelector('#capability-form');
      const input = document.querySelector('#capability-name');
      const success = document.querySelector('#capability-success');
      const submit = form?.querySelector('button[type="submit"], input[type="submit"]');
      const label = document.querySelector('label[for="capability-name"]');
      const rendered = ${ELEMENT_RENDERED_SOURCE};
      const focusSignature = ${FOCUS_SIGNATURE_SOURCE};
      const accessibleName = ${ACCESSIBLE_NAME_SOURCE};
      const pseudoText = ${PSEUDO_TEXT_SOURCE};
      if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      const policies = [...document.querySelectorAll('meta[http-equiv]')]
        .filter((meta) => meta.httpEquiv.toLowerCase() === 'content-security-policy')
        .map((meta) => meta.content.trim());
      const successPseudoTextBefore = pseudoText(success);
      return {
        missing: ['form', 'input', 'success', 'submit', 'label'].filter((key) => ({form, input, success, submit, label})[key] == null),
        textInputContract: input instanceof HTMLInputElement && input.type === 'text',
        inputAccessibleNameBefore: accessibleName(input),
        successVisibleBefore: rendered(success) && Boolean(
          success.textContent.trim().length > 0 || successPseudoTextBefore
        ),
        successTextBefore: success?.textContent?.trim() || '',
        successPseudoTextBefore,
        formVisibleBefore: [form, label, input, submit].every(rendered),
        urlBefore: location.href,
        contentSecurityPolicies: policies,
        beforeSubmission: {
          innerWidth: window.innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        },
        inputDisabled: Boolean(input?.disabled),
        inputReadOnly: Boolean(input?.readOnly),
        unfocusedStyles: {
          input: focusSignature(input),
          submit: focusSignature(submit),
        },
      };
    })()`);

    const inputKeyboardReachable = await tabUntil(
      client,
      `document.activeElement === document.querySelector('#capability-name')`,
    );
    const inputFocus = await evaluate(client, `(() => {
      const element = document.querySelector('#capability-name');
      const focusSignature = ${FOCUS_SIGNATURE_SOURCE};
      return {
        reachable: Boolean(element && document.activeElement === element),
        focusVisible: Boolean(element?.matches?.(':focus-visible')),
        focused: focusSignature(element),
      };
    })()`);
    inputFocus.unfocused = initial.unfocusedStyles?.input || null;
    inputFocus.changed = Boolean(
      inputFocus.reachable
      && inputFocus.focusVisible
      && focusSignatureRenderedChange(inputFocus.unfocused, inputFocus.focused),
    );

    if (inputKeyboardReachable) await typeWithKeyboard(client, 'Ada');

    const submitKeyboardReachable = await tabUntil(
      client,
      `(() => { const form = document.querySelector('#capability-form'); const submit = form?.querySelector('button[type="submit"], input[type="submit"]'); return document.activeElement === submit; })()`,
    );
    const submitFocus = await evaluate(client, `(() => {
      const form = document.querySelector('#capability-form');
      const element = form?.querySelector('button[type="submit"], input[type="submit"]');
      const focusSignature = ${FOCUS_SIGNATURE_SOURCE};
      return {
        reachable: Boolean(element && document.activeElement === element),
        focusVisible: Boolean(element?.matches?.(':focus-visible')),
        focused: focusSignature(element),
      };
    })()`);
    submitFocus.unfocused = initial.unfocusedStyles?.submit || null;
    submitFocus.changed = Boolean(
      submitFocus.reachable
      && submitFocus.focusVisible
      && focusSignatureRenderedChange(submitFocus.unfocused, submitFocus.focused),
    );

    if (submitKeyboardReachable) {
      await dispatchKey(client, 'Enter', 'Enter', 13);
    }

    const normalSubmissionMotion = await sampleMotionWindow(client);
    const remainingNormalObservationMs = Math.max(
      0,
      NETWORK_OBSERVATION_MS - normalSubmissionMotion.observedForMs,
    );
    if (remainingNormalObservationMs) {
      await new Promise((resolvePromise) => setTimeout(resolvePromise, remainingNormalObservationMs));
    }
    if (interceptionPromises.size) await Promise.allSettled([...interceptionPromises]);

    const snapshotExpression = (forbidden) => `(() => {
      const form = document.querySelector('#capability-form');
      const input = document.querySelector('#capability-name');
      const success = document.querySelector('#capability-success');
      const submit = form?.querySelector('button[type="submit"], input[type="submit"]');
      const label = document.querySelector('label[for="capability-name"]');
      const rendered = ${ELEMENT_RENDERED_SOURCE};
      const accessibleName = ${ACCESSIBLE_NAME_SOURCE};
      const pseudoText = ${PSEUDO_TEXT_SOURCE};
      const forbidden = ${JSON.stringify(forbidden || '')};
      let forbiddenTextVisible = false;
      if (forbidden) {
        forbiddenTextVisible = String(document.body?.innerText || '').includes(forbidden);
        if (!forbiddenTextVisible) {
          for (const element of document.querySelectorAll('*')) {
            for (const pseudo of ['::before', '::after']) {
              const style = getComputedStyle(element, pseudo);
              const content = String(style.content || '').replace(/^['"]|['"]$/g, '');
              if (content && content !== 'none' && content !== 'normal' && content.includes(forbidden)) {
                forbiddenTextVisible = true;
                break;
              }
            }
            if (forbiddenTextVisible) break;
          }
        }
      }
      const successPseudoText = pseudoText(success);
      return {
        successVisible: rendered(success) && Boolean(
          success.textContent.trim().length > 0 || successPseudoText
        ),
        successText: success?.textContent?.trim() || null,
        successPseudoText,
        submittedValue: input?.value || null,
        formVisibleAfter: [form, label, input, submit].every(rendered),
        textInputContract: input instanceof HTMLInputElement && input.type === 'text',
        inputAccessibleName: accessibleName(input),
        urlAfter: location.href,
        afterSubmission: {
          innerWidth: window.innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        },
        activeElementId: document.activeElement?.id || null,
        title: document.title,
        submission: window.__designStudioSubmissionTrace
          ? { ...window.__designStudioSubmissionTrace }
          : { trustedSubmit: false, causedSuccess: false, successObserved: false },
        forbiddenTextVisible,
      };
    })()`;

    const earlyAfter = await evaluate(client, snapshotExpression(forbiddenText));
    const normalPostSubmitMotion = await measureMotion(client);
    await client.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    const reducedPostSubmitMotion = await measureMotion(client);
    await new Promise((resolvePromise) => setTimeout(resolvePromise, NETWORK_OBSERVATION_MS));
    await client.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
    await new Promise((resolvePromise) => setTimeout(resolvePromise, NETWORK_OBSERVATION_MS));
    if (interceptionPromises.size) await Promise.allSettled([...interceptionPromises]);

    const popupAttempts = await evaluate(
      client,
      `Array.isArray(window.__designStudioPopupAttempts) ? window.__designStudioPopupAttempts.slice() : []`,
    );
    for (const url of popupAttempts || []) recordExternal(url, true);
    const guardedNetworkAttempts = await evaluate(
      client,
      `Array.isArray(window.__designStudioNetworkAttempts) ? window.__designStudioNetworkAttempts.slice() : []`,
    );
    for (const url of guardedNetworkAttempts || []) recordExternal(url, true);

    const policies = Array.isArray(initial.contentSecurityPolicies)
      ? initial.contentSecurityPolicies
      : [];
    const durableNetworkPolicy = policies.length === 1 && hasDurableNoNetworkPolicy(policies[0]);
    const focusStyleChanged = Boolean(inputFocus.changed && submitFocus.changed);

    const beforeScreenshot = await evaluate(client, snapshotExpression(forbiddenText));
    const screenshot = await client.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false, fromSurface: true });
    await writeFile(join(resolvedOutput, 'browser-after-submit.png'), Buffer.from(screenshot.data, 'base64'));
    const afterScreenshot = await evaluate(client, snapshotExpression(forbiddenText));
    const finalStateStable = [
      'successVisible',
      'successText',
      'successPseudoText',
      'submittedValue',
      'formVisibleAfter',
      'urlAfter',
      'forbiddenTextVisible',
      'inputAccessibleName',
    ].every((key) => JSON.stringify(beforeScreenshot[key]) === JSON.stringify(afterScreenshot[key]));

    const reducedSubmissionMotion = await replaySubmissionWithReducedMotion(
      client,
      frameId,
      html,
    );
    if (interceptionPromises.size) await Promise.allSettled([...interceptionPromises]);
    const replayPopupAttempts = await evaluate(
      client,
      `Array.isArray(window.__designStudioPopupAttempts) ? window.__designStudioPopupAttempts.slice() : []`,
    ).catch(() => []);
    for (const url of replayPopupAttempts || []) recordExternal(url, true);
    const replayGuardedNetworkAttempts = await evaluate(
      client,
      `Array.isArray(window.__designStudioNetworkAttempts) ? window.__designStudioNetworkAttempts.slice() : []`,
    ).catch(() => []);
    for (const url of replayGuardedNetworkAttempts || []) recordExternal(url, true);

    const motionSupported = Boolean(
      motionPairSupported(normalMotion, reducedMotion)
      && motionPairSupported(normalPostSubmitMotion, reducedPostSubmitMotion)
      && reducedSubmissionMotion.performed
      && reducedSubmissionMotion.contractPassed
      && motionPairSupported(normalSubmissionMotion, reducedSubmissionMotion)
    );

    const interaction = {
      ...initial,
      ...afterScreenshot,
      focus: {
        visible: focusStyleChanged,
        input: inputFocus,
        submit: submitFocus,
        inputKeyboardReachable,
        submitKeyboardReachable,
      },
      focusStyleChanged,
      finalStateStable,
      reducedMotion: Boolean(
        reducedMotion.prefersReducedMotion
        && reducedPostSubmitMotion.prefersReducedMotion
        && reducedSubmissionMotion.prefersReducedMotion
      ),
      motion: {
        supported: motionSupported,
        normalMaxMs: normalMotion.maxMs,
        reducedMaxMs: reducedMotion.maxMs,
        normalPostSubmitMaxMs: normalPostSubmitMotion.maxMs,
        reducedPostSubmitMaxMs: reducedPostSubmitMotion.maxMs,
        normalSubmissionMaxMs: normalSubmissionMotion.maxMs,
        reducedSubmissionMaxMs: reducedSubmissionMotion.maxMs,
        reducedSubmissionReplayPerformed: reducedSubmissionMotion.performed,
        reducedSubmissionReplayContractPassed: reducedSubmissionMotion.contractPassed,
        reducedSubmissionReplayError: reducedSubmissionMotion.error,
        reducedSubmissionReplayState: reducedSubmissionMotion.replayState || null,
        normalActiveElementCount: normalMotion.activeElementCount,
        reducedActiveElementCount: reducedMotion.activeElementCount,
        normalPostSubmitActiveElementCount: normalPostSubmitMotion.activeElementCount,
        reducedPostSubmitActiveElementCount: reducedPostSubmitMotion.activeElementCount,
        normalSubmissionActiveElementCount: normalSubmissionMotion.activeElementCount,
        reducedSubmissionActiveElementCount: reducedSubmissionMotion.activeElementCount,
        normalSamples: normalMotion.samples,
        reducedSamples: reducedMotion.samples,
        normalPostSubmitSamples: normalPostSubmitMotion.samples,
        reducedPostSubmitSamples: reducedPostSubmitMotion.samples,
        normalSubmissionSamples: normalSubmissionMotion.samples,
        reducedSubmissionSamples: reducedSubmissionMotion.samples,
      },
    };

    const requests = [...requestUrls].sort();
    const externalRequests = [...externalRequestUrls].sort();
    const blockedRequests = [...blockedRequestUrls].sort();
    const failures = [];
    if (interaction.missing?.length) failures.push(`missing required elements: ${interaction.missing.join(', ')}`);
    if (!interaction.textInputContract) failures.push('capability-name is not a text input');
    if (!interaction.inputAccessibleNameBefore || !interaction.inputAccessibleName) failures.push('capability-name has no accessible label');
    if (!interaction.formVisibleBefore) failures.push('form controls were not visible before submission');
    if (interaction.successVisibleBefore) failures.push('success state was visible before submission');
    if (interaction.successTextBefore) failures.push('success state contained content before submission');
    if (!interaction.submission?.trustedSubmit) failures.push('no trusted keyboard submission was observed');
    if (!interaction.submission?.causedSuccess) failures.push('success transition was not caused by the trusted submission');
    if (!interaction.successVisible) {
      if (earlyAfter.successVisible || interaction.submission?.successObserved) {
        failures.push('success state did not remain visible at screenshot time');
      } else {
        failures.push('success state did not become visible');
      }
    }
    if (
      interaction.successText !== 'Capability complete'
      || interaction.successPseudoText
    ) failures.push('success state text is not exact');
    if (!interaction.formVisibleAfter) failures.push('form controls did not remain visible after submission');
    if (interaction.submittedValue !== 'Ada') failures.push('text input did not accept real keyboard input');
    if (interaction.urlAfter !== interaction.urlBefore) failures.push('submission changed the document URL');
    if (interaction.beforeSubmission?.innerWidth !== width || interaction.afterSubmission?.innerWidth !== width) failures.push(`viewport width did not remain ${width}`);
    if (interaction.beforeSubmission?.scrollWidth > interaction.beforeSubmission?.clientWidth) failures.push('document has horizontal overflow before submission');
    if (interaction.afterSubmission?.scrollWidth > interaction.afterSubmission?.clientWidth) failures.push('document has horizontal overflow after submission');
    if (!interaction.focus.visible) {
      failures.push('keyboard focus is not visibly indicated');
      failures.push('keyboard focus produced no visual style change');
      failures.push('keyboard focus produced no rendered visual change');
    }
    if (!interaction.reducedMotion) failures.push('reduced-motion emulation was not visible to the page');
    if (reducedSubmissionMotion.error) {
      failures.push(`reduced-motion submission replay did not run: ${reducedSubmissionMotion.error}`);
    } else if (!motionSupported) {
      failures.push('reduced-motion path did not suppress active motion');
    }
    if (!durableNetworkPolicy) failures.push('document lacks a durable no-network content security policy');
    if (externalRequests.length) failures.push('external network request attempted');
    if (externalRequests.some((url) => !blockedRequestUrls.has(url))) failures.push('external network request was not blocked before transport');
    if (interaction.forbiddenTextVisible) failures.push('forbidden text became visible');
    if (!interaction.finalStateStable) failures.push('rendered state changed while the screenshot was captured');

    return {
      schemaVersion: 1,
      status: failures.length ? 'failed' : 'passed',
      chrome: { path: chromePath },
      url: interaction.urlAfter || null,
      viewport: { width, height },
      interaction,
      network: {
        durablePolicy: durableNetworkPolicy,
        contentSecurityPolicy: policies[0] || '',
        contentSecurityPolicies: policies,
        requests,
        externalRequests,
        blockedRequests,
        blockedPopupTargets: [...blockedPopupTargets].sort(),
        blockedAuxiliaryTargets: [...blockedAuxiliaryTargets].sort(),
        popupAttempts: [...(popupAttempts || [])],
        guardedNetworkAttempts: [...(guardedNetworkAttempts || [])],
        observationMs: NETWORK_OBSERVATION_MS,
      },
      screenshot: 'browser-after-submit.png',
      failures,
    };
  } finally {
    try {
      client?.close();
    } catch (error) {
      if (process.env.DEBUG_BROWSER_PROBE) {
        process.stderr.write(`failed to close DevTools client: ${error?.message || String(error)}\n`);
      }
    }
    if (chrome) {
      try {
        await stopChrome(chrome);
      } catch (error) {
        if (process.env.DEBUG_BROWSER_PROBE) {
          process.stderr.write(`failed to stop Chrome cleanly: ${error?.message || String(error)}\n`);
        }
      }
    }
    await removeBrowserProfileBestEffort(userDataDir, {
      onError: (error) => {
        if (process.env.DEBUG_BROWSER_PROBE) {
          process.stderr.write(`failed to remove browser profile: ${error?.message || String(error)}\n`);
        }
      },
    });
    if (stderr && process.env.DEBUG_BROWSER_PROBE) process.stderr.write(stderr);
  }
}
async function main() {
  let args;
  let report;
  try {
    args = parseArgs(process.argv.slice(2));
    report = await runBrowserProbe(args);
  } catch (error) {
    report = {
      schemaVersion: 1,
      status: error instanceof BrowserBlockedError ? 'blocked' : 'failed',
      error: `${error?.name || 'Error'}: ${error?.message || String(error)}`,
      failures: [],
    };
  }

  const outputDir = resolve(args?.outputDir || process.cwd());
  await mkdir(outputDir, { recursive: true });
  await writeFile(join(outputDir, 'browser-report.json'), `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify({ status: report.status, report: join(outputDir, 'browser-report.json') })}\n`);
  process.exitCode = report.status === 'passed' ? 0 : report.status === 'blocked' ? 2 : 1;
}

await main();
