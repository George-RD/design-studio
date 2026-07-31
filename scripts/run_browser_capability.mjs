#!/usr/bin/env node
import { spawn, spawnSync } from 'node:child_process';
import { lstat, mkdir, mkdtemp, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import process from 'node:process';

class BrowserContractError extends Error {}
class BrowserBlockedError extends Error {}

const NETWORK_OBSERVATION_MS = 1300;
const MOTION_LIMIT_MS = 50;

function parseArgs(argv) {
  const args = { root: null, outputDir: null, entrypoint: 'index.html', width: 390, height: 844 };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (key === '--root') args.root = value;
    else if (key === '--output-dir') args.outputDir = value;
    else if (key === '--entrypoint') args.entrypoint = value;
    else if (key === '--width') args.width = Number(value);
    else if (key === '--height') args.height = Number(value);
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
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
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
    await new Promise((resolvePromise, reject) => {
      this.socket.addEventListener('open', resolvePromise, { once: true });
      this.socket.addEventListener('error', () => reject(new BrowserBlockedError('DevTools websocket failed to open')), { once: true });
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
      if (message.error) pending.reject(new BrowserContractError(`${pending.method}: ${message.error.message}`));
      else pending.resolve(message.result || {});
    });
    this.socket.addEventListener('close', () => {
      for (const pending of this.pending.values()) pending.reject(new BrowserBlockedError('DevTools websocket closed unexpectedly'));
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
      this.pending.set(id, { method, resolve: resolvePromise, reject });
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
  await client.send('Input.dispatchKeyEvent', { type: 'keyDown', ...params });
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
  return evaluate(client, `(async () => {
    await new Promise((resolvePromise) => requestAnimationFrame(() => requestAnimationFrame(resolvePromise)));
    const parseTimes = (value) => String(value || '').split(',').map((part) => {
      const text = part.trim();
      if (text.endsWith('ms')) return Number.parseFloat(text) || 0;
      if (text.endsWith('s')) return (Number.parseFloat(text) || 0) * 1000;
      return 0;
    });
    const maximum = (values) => values.length ? Math.max(...values) : 0;
    let maxMs = 0;
    let activeElementCount = 0;
    const samples = [];
    for (const element of document.querySelectorAll('*')) {
      const style = getComputedStyle(element);
      const transitionMs = maximum(parseTimes(style.transitionDuration)) + Math.max(0, maximum(parseTimes(style.transitionDelay)));
      const animationMs = maximum(parseTimes(style.animationDuration)) + Math.max(0, maximum(parseTimes(style.animationDelay)));
      const elementMaxMs = Math.max(transitionMs, animationMs);
      if (elementMaxMs > 1) {
        activeElementCount += 1;
        maxMs = Math.max(maxMs, elementMaxMs);
        if (samples.length < 8) samples.push({ tag: element.tagName.toLowerCase(), id: element.id || null, maxMs: elementMaxMs });
      }
    }
    return {
      prefersReducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
      maxMs,
      activeElementCount,
      samples,
    };
  })()`);
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
  promise.finally(() => set.delete(promise));
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
  const record = (value) => attempts.push(String(value ?? 'about:blank'));
  Object.defineProperty(window, '__designStudioPopupAttempts', {
    configurable: false,
    enumerable: false,
    get: () => attempts.slice(),
  });
  Object.defineProperty(window, '__designStudioPopupGuardInstalled', {
    configurable: false,
    enumerable: false,
    value: true,
  });
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

async function runBrowserProbe({ root, outputDir, entrypoint, width, height }) {
  const resolvedRoot = resolve(root);
  const resolvedOutput = resolve(outputDir);
  const entryPath = safePath(resolvedRoot, entrypoint);
  await requireRegularFileInsideRoot(resolvedRoot, entryPath);
  const html = await readFile(entryPath, 'utf8');
  await mkdir(resolvedOutput, { recursive: true });

  const chromePath = findChrome();
  const userDataDir = await mkdtemp(join(tmpdir(), 'design-studio-browser-'));
  const chrome = spawn(chromePath, [
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
  let stderr = '';
  chrome.stderr.setEncoding('utf8');
  chrome.stderr.on('data', (chunk) => { stderr += chunk; });

  let client;
  try {
    const devToolsPort = await waitForDevTools(userDataDir, chrome);
    const target = await getPageTarget(devToolsPort);
    client = new CdpClient(target.webSocketDebuggerUrl);
    await client.connect();

    const requestUrls = new Set();
    const externalRequestUrls = new Set();
    const blockedRequestUrls = new Set();
    const blockedPopupTargets = new Set();
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
    const containPopupTarget = (info) => {
      if (!info || info.type !== 'page' || !info.targetId || info.targetId === target.id) return;
      if (typeof info.url === 'string' && info.url) recordExternal(info.url, true);
      blockedPopupTargets.add(info.targetId);
      const close = Promise.race([
        client.send('Target.closeTarget', { targetId: info.targetId }).catch(() => {}),
        new Promise((resolvePromise) => setTimeout(resolvePromise, 500)),
      ]);
      trackPromise(interceptionPromises, close);
    };
    client.on('Target.targetCreated', (params) => containPopupTarget(params?.targetInfo));
    client.on('Target.targetInfoChanged', (params) => containPopupTarget(params?.targetInfo));


    await client.send('Page.enable');
    await client.send('Runtime.enable');
    await client.send('Network.enable');
    await client.send('Fetch.enable', { patterns: [{ urlPattern: '*', requestStage: 'Request' }] });
    await client.send('Network.setBlockedURLs', { urls: ['ws://*', 'wss://*', 'ftp://*'] });
    await client.send('Target.setDiscoverTargets', { discover: true });
    await client.send('Page.addScriptToEvaluateOnNewDocument', { source: POPUP_GUARD_SOURCE });
    await evaluate(client, POPUP_GUARD_SOURCE);
    await client.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
    await client.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
    const frameTree = await client.send('Page.getFrameTree');
    const frameId = frameTree.frameTree?.frame?.id;
    if (!frameId) throw new BrowserBlockedError('Chrome exposed no main frame');
    await client.send('Page.setDocumentContent', { frameId, html });
    await evaluate(client, POPUP_GUARD_SOURCE);

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
      const rendered = (element) => {
        if (!element) return false;
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return !element.hidden
          && style.display !== 'none'
          && style.visibility !== 'hidden'
          && Number.parseFloat(style.opacity || '1') > 0.01
          && rect.width > 0
          && rect.height > 0
          && rect.bottom > 0
          && rect.right > 0
          && rect.top < window.innerHeight
          && rect.left < window.innerWidth;
      };
      const styleSignature = (element) => {
        if (!element) return null;
        const style = getComputedStyle(element);
        return {
          outlineStyle: style.outlineStyle,
          outlineWidth: style.outlineWidth,
          outlineColor: style.outlineColor,
          outlineOffset: style.outlineOffset,
          boxShadow: style.boxShadow,
          borderColor: style.borderColor,
          borderWidth: style.borderWidth,
          backgroundColor: style.backgroundColor,
          color: style.color,
          filter: style.filter,
        };
      };
      if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      return {
        missing: ['form', 'input', 'success', 'submit', 'label'].filter((key) => ({form, input, success, submit, label})[key] == null),
        successVisibleBefore: rendered(success) && success.textContent.trim().length > 0,
        successTextBefore: success?.textContent?.trim() || '',
        formVisibleBefore: [form, label, input, submit].every(rendered),
        urlBefore: location.href,
        beforeSubmission: {
          innerWidth: window.innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        },
        inputDisabled: Boolean(input?.disabled),
        inputReadOnly: Boolean(input?.readOnly),
        unfocusedStyles: {
          input: styleSignature(input),
          submit: styleSignature(submit),
        },
      };
    })()`);

    const inputKeyboardReachable = await tabUntil(
      client,
      `document.activeElement === document.querySelector('#capability-name')`,
    );
    const inputFocus = await evaluate(client, `(() => {
      const element = document.querySelector('#capability-name');
      if (!element || document.activeElement !== element) return { reachable: false, changed: false };
      const style = getComputedStyle(element);
      const focused = {
        outlineStyle: style.outlineStyle,
        outlineWidth: style.outlineWidth,
        outlineColor: style.outlineColor,
        outlineOffset: style.outlineOffset,
        boxShadow: style.boxShadow,
        borderColor: style.borderColor,
        borderWidth: style.borderWidth,
        backgroundColor: style.backgroundColor,
        color: style.color,
        filter: style.filter,
      };
      const unfocused = ${JSON.stringify(null)};
      return { reachable: true, focused };
    })()`);
    inputFocus.unfocused = initial.unfocusedStyles?.input || null;
    inputFocus.changed = Boolean(
      inputFocus.reachable
      && JSON.stringify(inputFocus.unfocused) !== JSON.stringify(inputFocus.focused || null)
    );

    const submitKeyboardReachable = await tabUntil(
      client,
      `(() => { const form = document.querySelector('#capability-form'); const submit = form?.querySelector('button[type="submit"], input[type="submit"]'); return document.activeElement === submit; })()`,
    );
    const submitFocus = await evaluate(client, `(() => {
      const form = document.querySelector('#capability-form');
      const element = form?.querySelector('button[type="submit"], input[type="submit"]');
      if (!element || document.activeElement !== element) return { reachable: false, changed: false };
      const style = getComputedStyle(element);
      return {
        reachable: true,
        focused: {
          outlineStyle: style.outlineStyle,
          outlineWidth: style.outlineWidth,
          outlineColor: style.outlineColor,
          outlineOffset: style.outlineOffset,
          boxShadow: style.boxShadow,
          borderColor: style.borderColor,
          borderWidth: style.borderWidth,
          backgroundColor: style.backgroundColor,
          color: style.color,
          filter: style.filter,
        },
      };
    })()`);
    submitFocus.unfocused = initial.unfocusedStyles?.submit || null;
    submitFocus.changed = Boolean(
      submitFocus.reachable
      && JSON.stringify(submitFocus.unfocused) !== JSON.stringify(submitFocus.focused || null)
    );

    const returnedToInput = await tabUntil(
      client,
      `document.activeElement === document.querySelector('#capability-name')`,
      { reverse: true },
    );
    if (inputKeyboardReachable && returnedToInput) {
      await client.send('Input.insertText', { text: 'Ada' });
      await evaluate(client, `(() => {
        const form = document.querySelector('#capability-form');
        const submit = form?.querySelector('button[type="submit"], input[type="submit"]');
        if (form && submit && typeof form.requestSubmit === 'function') form.requestSubmit(submit);
        else if (submit instanceof HTMLElement) submit.click();
        return true;
      })()`);
    }

    await new Promise((resolvePromise) => setTimeout(resolvePromise, NETWORK_OBSERVATION_MS));
    if (interceptionPromises.size) await Promise.allSettled([...interceptionPromises]);

    const after = await evaluate(client, `(() => {
      const form = document.querySelector('#capability-form');
      const input = document.querySelector('#capability-name');
      const success = document.querySelector('#capability-success');
      const submit = form?.querySelector('button[type="submit"], input[type="submit"]');
      const label = document.querySelector('label[for="capability-name"]');
      const rendered = (element) => {
        if (!element) return false;
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return !element.hidden
          && style.display !== 'none'
          && style.visibility !== 'hidden'
          && Number.parseFloat(style.opacity || '1') > 0.01
          && rect.width > 0
          && rect.height > 0
          && rect.bottom > 0
          && rect.right > 0
          && rect.top < window.innerHeight
          && rect.left < window.innerWidth;
      };
      return {
        successVisible: rendered(success) && success.textContent.trim().length > 0,
        successText: success?.textContent?.trim() || null,
        submittedValue: input?.value || null,
        formVisibleAfter: [form, label, input, submit].every(rendered),
        urlAfter: location.href,
        afterSubmission: {
          innerWidth: window.innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        },
        activeElementId: document.activeElement?.id || null,
        title: document.title,
      };
    })()`);

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

    const focusStyleChanged = Boolean(inputFocus.changed && submitFocus.changed);
    const motionSupported = Boolean(
      motionPairSupported(normalMotion, reducedMotion)
      && motionPairSupported(normalPostSubmitMotion, reducedPostSubmitMotion)
    );
    const interaction = {
      ...initial,
      ...after,
      focus: {
        visible: focusStyleChanged,
        input: inputFocus,
        submit: submitFocus,
        inputKeyboardReachable,
        submitKeyboardReachable,
      },
      focusStyleChanged,
      reducedMotion: Boolean(
        reducedMotion.prefersReducedMotion
        && reducedPostSubmitMotion.prefersReducedMotion
      ),
      motion: {
        supported: motionSupported,
        normalMaxMs: normalMotion.maxMs,
        reducedMaxMs: reducedMotion.maxMs,
        normalPostSubmitMaxMs: normalPostSubmitMotion.maxMs,
        reducedPostSubmitMaxMs: reducedPostSubmitMotion.maxMs,
        normalActiveElementCount: normalMotion.activeElementCount,
        reducedActiveElementCount: reducedMotion.activeElementCount,
        normalPostSubmitActiveElementCount: normalPostSubmitMotion.activeElementCount,
        reducedPostSubmitActiveElementCount: reducedPostSubmitMotion.activeElementCount,
        normalSamples: normalMotion.samples,
        reducedSamples: reducedMotion.samples,
        normalPostSubmitSamples: normalPostSubmitMotion.samples,
        reducedPostSubmitSamples: reducedPostSubmitMotion.samples,
      },
    };

    const requests = [...requestUrls].sort();
    const externalRequests = [...externalRequestUrls].sort();
    const blockedRequests = [...blockedRequestUrls].sort();
    const screenshot = await client.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false, fromSurface: true });
    await writeFile(join(resolvedOutput, 'browser-after-submit.png'), Buffer.from(screenshot.data, 'base64'));

    const failures = [];
    if (interaction.missing?.length) failures.push(`missing required elements: ${interaction.missing.join(', ')}`);
    if (!interaction.formVisibleBefore) failures.push('form controls were not visible before submission');
    if (interaction.successVisibleBefore) failures.push('success state was visible before submission');
    if (interaction.successTextBefore) failures.push('success state contained content before submission');
    if (!interaction.successVisible) failures.push('success state did not become visible');
    if (interaction.successText !== 'Capability complete') failures.push('success state text is not exact');
    if (!interaction.formVisibleAfter) failures.push('form controls did not remain visible after submission');
    if (interaction.submittedValue !== 'Ada') failures.push('text input did not accept real keyboard input');
    if (interaction.urlAfter !== interaction.urlBefore) failures.push('submission changed the document URL');
    if (interaction.beforeSubmission?.innerWidth !== width || interaction.afterSubmission?.innerWidth !== width) failures.push(`viewport width did not remain ${width}`);
    if (interaction.beforeSubmission?.scrollWidth > interaction.beforeSubmission?.clientWidth) failures.push('document has horizontal overflow before submission');
    if (interaction.afterSubmission?.scrollWidth > interaction.afterSubmission?.clientWidth) failures.push('document has horizontal overflow after submission');
    if (!interaction.focus.visible) {
      failures.push('keyboard focus is not visibly indicated');
      failures.push('keyboard focus produced no visual style change');
    }
    if (!interaction.reducedMotion) failures.push('reduced-motion emulation was not visible to the page');
    if (!motionSupported) failures.push('reduced-motion path did not suppress active motion');
    if (externalRequests.length) failures.push('external network request attempted');
    if (externalRequests.some((url) => !blockedRequestUrls.has(url))) failures.push('external network request was not blocked before transport');

    return {
      schemaVersion: 1,
      status: failures.length ? 'failed' : 'passed',
      chrome: { path: chromePath },
      url: interaction.urlAfter || null,
      viewport: { width, height },
      interaction,
      network: {
        requests,
        externalRequests,
        blockedRequests,
        blockedPopupTargets: [...blockedPopupTargets].sort(),
        popupAttempts: [...(popupAttempts || [])],
        observationMs: NETWORK_OBSERVATION_MS,
      },
      screenshot: 'browser-after-submit.png',
      failures,
    };
  } finally {
    client?.close();
    await stopChrome(chrome);
    await rm(userDataDir, { recursive: true, force: true });
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
