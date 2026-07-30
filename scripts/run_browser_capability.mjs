#!/usr/bin/env node
import { spawn, spawnSync } from 'node:child_process';
import { mkdir, mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import process from 'node:process';

class BrowserContractError extends Error {}
class BrowserBlockedError extends Error {}

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
          listener(message.params || {});
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

  send(method, params = {}) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return Promise.reject(new BrowserBlockedError('DevTools websocket is not open'));
    }
    const id = this.nextId;
    this.nextId += 1;
    return new Promise((resolvePromise, reject) => {
      this.pending.set(id, { method, resolve: resolvePromise, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
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

function isExternalNetworkUrl(value) {
  try {
    return ['http:', 'https:', 'ws:', 'wss:', 'ftp:'].includes(new URL(value).protocol);
  } catch {
    return true;
  }
}

async function runBrowserProbe({ root, outputDir, entrypoint, width, height }) {
  const resolvedRoot = resolve(root);
  const resolvedOutput = resolve(outputDir);
  const entryPath = safePath(resolvedRoot, entrypoint);
  const entryInfo = await stat(entryPath);
  if (!entryInfo.isFile()) throw new BrowserContractError('entrypoint is not a file');
  const html = await readFile(entryPath, 'utf8');
  await mkdir(resolvedOutput, { recursive: true });

  const chromePath = findChrome();
  const userDataDir = await mkdtemp(join(tmpdir(), 'design-studio-browser-'));
  const chrome = spawn(chromePath, [
    '--headless=new',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
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
    client.on('Network.requestWillBeSent', (params) => {
      const url = params?.request?.url;
      if (typeof url === 'string' && url) requestUrls.add(url);
    });

    await client.send('Page.enable');
    await client.send('Runtime.enable');
    await client.send('Network.enable');
    await client.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
    await client.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
    const frameTree = await client.send('Page.getFrameTree');
    const frameId = frameTree.frameTree?.frame?.id;
    if (!frameId) throw new BrowserBlockedError('Chrome exposed no main frame');
    await client.send('Page.setDocumentContent', { frameId, html });

    const normalMotion = await measureMotion(client);
    await client.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    const reducedMotion = await measureMotion(client);
    const motionSupported = normalMotion.maxMs <= 50 || reducedMotion.maxMs <= 50;

    const interaction = await evaluate(client, `(async () => {
      const form = document.querySelector('#capability-form');
      const input = document.querySelector('#capability-name');
      const success = document.querySelector('#capability-success');
      const submit = form?.querySelector('button[type="submit"], input[type="submit"]');
      const visible = (element) => {
        if (!element) return false;
        const style = getComputedStyle(element);
        return element.textContent.trim().length > 0 && !element.hidden && style.display !== 'none' && style.visibility !== 'hidden' && Number.parseFloat(style.opacity || '1') > 0.01 && element.getBoundingClientRect().height > 0;
      };
      const urlBefore = location.href;
      const successVisibleBefore = visible(success);
      if (!form || !input || !success || !submit) {
        return {
          missing: ['form', 'input', 'success', 'submit'].filter((key) => ({form, input, success, submit})[key] == null),
          successVisibleBefore,
          successVisible: visible(success),
          successText: success?.textContent?.trim() || null,
          submittedValue: input?.value || null,
          urlBefore,
          urlAfter: location.href,
          innerWidth: window.innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
          reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
        };
      }
      input.focus();
      input.value = 'Ada';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      if (typeof form.requestSubmit === 'function') form.requestSubmit(submit);
      else submit.click();
      await new Promise((resolvePromise) => setTimeout(resolvePromise, 250));
      return {
        missing: [],
        successVisibleBefore,
        successVisible: visible(success),
        successText: success.textContent.trim(),
        submittedValue: input.value,
        urlBefore,
        urlAfter: location.href,
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
        activeElementId: document.activeElement?.id || null,
        title: document.title,
      };
    })()`);
    interaction.motion = {
      supported: motionSupported,
      normalMaxMs: normalMotion.maxMs,
      reducedMaxMs: reducedMotion.maxMs,
      normalActiveElementCount: normalMotion.activeElementCount,
      reducedActiveElementCount: reducedMotion.activeElementCount,
      normalSamples: normalMotion.samples,
      reducedSamples: reducedMotion.samples,
    };

    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
    const requests = [...requestUrls].sort();
    const externalRequests = requests.filter(isExternalNetworkUrl);
    const screenshot = await client.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false, fromSurface: true });
    await writeFile(join(resolvedOutput, 'browser-after-submit.png'), Buffer.from(screenshot.data, 'base64'));

    const failures = [];
    if (interaction?.missing?.length) failures.push(`missing required elements: ${interaction.missing.join(', ')}`);
    if (interaction?.successVisibleBefore) failures.push('success state was visible before submission');
    if (!interaction?.successVisible) failures.push('success state did not become visible');
    if (interaction?.successText !== 'Capability complete') failures.push('success state text is not exact');
    if (interaction?.submittedValue !== 'Ada') failures.push('form value was not preserved through local submission');
    if (interaction?.urlAfter !== interaction?.urlBefore) failures.push('submission changed the document URL');
    if (interaction?.innerWidth !== width) failures.push(`viewport width was ${interaction?.innerWidth}, expected ${width}`);
    if (interaction?.scrollWidth > interaction?.clientWidth) failures.push('document has horizontal overflow');
    if (!interaction?.reducedMotion) failures.push('reduced-motion emulation was not visible to the page');
    if (!motionSupported) failures.push('reduced-motion path did not suppress active motion');
    if (externalRequests.length) failures.push('external network request observed');

    return {
      schemaVersion: 1,
      status: failures.length ? 'failed' : 'passed',
      chrome: { path: chromePath },
      url: interaction?.urlAfter || null,
      viewport: { width, height },
      interaction,
      network: { requests, externalRequests },
      screenshot: 'browser-after-submit.png',
      failures,
    };
  } finally {
    client?.close();
    if (chrome.exitCode === null) chrome.kill('SIGTERM');
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
    if (chrome.exitCode === null) chrome.kill('SIGKILL');
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
