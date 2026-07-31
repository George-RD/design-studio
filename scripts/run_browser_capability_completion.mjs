#!/usr/bin/env node
import { spawn, spawnSync } from 'node:child_process';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import process from 'node:process';

const BASE_BROWSER_SCRIPT = new URL('./run_browser_capability.mjs', import.meta.url);

class CompletionProbeError extends Error {}

function parseArgs(argv) {
  const args = {
    root: null,
    outputDir: null,
    entrypoint: 'index.html',
    width: 390,
    height: 844,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (key === '--root') args.root = value;
    else if (key === '--output-dir') args.outputDir = value;
    else if (key === '--entrypoint') args.entrypoint = value;
    else if (key === '--width') args.width = Number(value);
    else if (key === '--height') args.height = Number(value);
    else throw new CompletionProbeError(`unknown or incomplete argument: ${key}`);
    index += 1;
  }
  if (!args.root || !args.outputDir) {
    throw new CompletionProbeError('--root and --output-dir are required');
  }
  return args;
}

function findChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  for (const candidate of [
    'google-chrome-stable',
    'google-chrome',
    'chromium',
    'chromium-browser',
  ]) {
    const found = spawnSync('sh', ['-lc', `command -v ${candidate}`], {
      encoding: 'utf8',
    });
    if (found.status === 0 && found.stdout.trim()) return found.stdout.trim();
  }
  throw new CompletionProbeError('Chrome or Chromium is not installed');
}

async function waitForDevTools(userDataDir, chrome, timeoutMs = 15000) {
  const activePort = join(userDataDir, 'DevToolsActivePort');
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (chrome.exitCode !== null) {
      throw new CompletionProbeError(
        `Chrome exited before DevTools was ready (status ${chrome.exitCode})`,
      );
    }
    try {
      const [portLine] = (await readFile(activePort, 'utf8'))
        .trim()
        .split(/\r?\n/);
      const port = Number(portLine);
      if (Number.isInteger(port) && port > 0) return port;
    } catch (error) {
      if (error?.code !== 'ENOENT') throw error;
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
  }
  throw new CompletionProbeError('Chrome DevTools did not become ready');
}

async function getPageTarget(port, timeoutMs = 10000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`);
      if (response.ok) {
        const targets = await response.json();
        const page = targets.find(
          (target) => target.type === 'page' && target.webSocketDebuggerUrl,
        );
        if (page) return page;
      }
    } catch {
      // Retry while Chrome starts.
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
  }
  throw new CompletionProbeError('Chrome exposed no debuggable page target');
}

class CdpClient {
  constructor(url) {
    this.url = url;
    this.socket = null;
    this.nextId = 1;
    this.pending = new Map();
  }

  async connect() {
    this.socket = new WebSocket(this.url);
    await new Promise((resolvePromise, reject) => {
      this.socket.addEventListener('open', resolvePromise, { once: true });
      this.socket.addEventListener(
        'error',
        () => reject(new CompletionProbeError('DevTools websocket failed to open')),
        { once: true },
      );
    });
    this.socket.addEventListener('message', (event) => {
      const message = JSON.parse(String(event.data));
      if (!message.id) return;
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) {
        pending.reject(
          new CompletionProbeError(
            `${pending.method}: ${message.error.message}`,
          ),
        );
      } else {
        pending.resolve(message.result || {});
      }
    });
  }

  send(method, params = {}) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return Promise.reject(
        new CompletionProbeError('DevTools websocket is not open'),
      );
    }
    const id = this.nextId;
    this.nextId += 1;
    return new Promise((resolvePromise, reject) => {
      this.pending.set(id, {
        method,
        resolve: resolvePromise,
        reject,
      });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    if (this.socket && this.socket.readyState <= WebSocket.OPEN) {
      this.socket.close();
    }
  }
}

async function evaluate(client, expression) {
  const result = await client.send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true,
  });
  if (result.exceptionDetails) {
    throw new CompletionProbeError('page evaluation raised an exception');
  }
  return result.result?.value;
}

async function inspectCompletionState({ html, width, height }) {
  const chromePath = findChrome();
  const userDataDir = await mkdtemp(
    join(tmpdir(), 'design-studio-completion-browser-'),
  );
  const chrome = spawn(
    chromePath,
    [
      '--headless=new',
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-background-networking',
      '--disable-component-update',
      '--remote-debugging-port=0',
      `--user-data-dir=${userDataDir}`,
      `--window-size=${width},${height}`,
      'about:blank',
    ],
    { stdio: ['ignore', 'ignore', 'ignore'] },
  );

  let client;
  try {
    const port = await waitForDevTools(userDataDir, chrome);
    const target = await getPageTarget(port);
    client = new CdpClient(target.webSocketDebuggerUrl);
    await client.connect();
    await client.send('Page.enable');
    await client.send('Runtime.enable');
    await client.send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: false,
    });
    const frameTree = await client.send('Page.getFrameTree');
    const frameId = frameTree.frameTree?.frame?.id;
    if (!frameId) throw new CompletionProbeError('Chrome exposed no main frame');
    await client.send('Page.setDocumentContent', { frameId, html });

    const initial = await evaluate(
      client,
      `(() => {
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
            && rect.height > 0;
        };
        return {
          successTextBefore: success?.textContent?.trim() || '',
          formVisibleBefore: [form, label, input, submit].every(rendered),
        };
      })()`,
    );

    await evaluate(
      client,
      `(() => {
        const form = document.querySelector('#capability-form');
        const input = document.querySelector('#capability-name');
        const submit = form?.querySelector('button[type="submit"], input[type="submit"]');
        if (input) {
          input.value = 'Ada';
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
        if (form && submit && typeof form.requestSubmit === 'function') {
          form.requestSubmit(submit);
        } else if (submit instanceof HTMLElement) {
          submit.click();
        }
        return true;
      })()`,
    );
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));

    const after = await evaluate(
      client,
      `(() => {
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
            && rect.height > 0;
        };
        return {
          successText: success?.textContent?.trim() || null,
          formVisibleAfter: [form, label, input, submit].every(rendered),
        };
      })()`,
    );

    return { ...initial, ...after };
  } finally {
    client?.close();
    if (chrome.exitCode === null) chrome.kill('SIGTERM');
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
    if (chrome.exitCode === null) chrome.kill('SIGKILL');
    await rm(userDataDir, { recursive: true, force: true });
  }
}

async function main() {
  let args;
  let outputDir;
  try {
    args = parseArgs(process.argv.slice(2));
    outputDir = resolve(args.outputDir);
    await mkdir(outputDir, { recursive: true });

    const base = spawnSync(
      process.execPath,
      [BASE_BROWSER_SCRIPT.pathname, ...process.argv.slice(2)],
      {
        encoding: 'utf8',
        timeout: 45000,
        env: process.env,
      },
    );
    if (base.error) throw base.error;

    const reportPath = join(outputDir, 'browser-report.json');
    const report = JSON.parse(await readFile(reportPath, 'utf8'));
    if (report.status === 'passed') {
      const entryPath = resolve(args.root, args.entrypoint);
      const html = await readFile(entryPath, 'utf8');
      const completion = await inspectCompletionState({
        html,
        width: args.width,
        height: args.height,
      });
      const failures = [...(report.failures || [])];
      if (!completion.formVisibleBefore) {
        failures.push('form controls were not visible before submission');
      }
      if (completion.successTextBefore) {
        failures.push('success state contained content before submission');
      }
      if (!completion.formVisibleAfter) {
        failures.push('form controls did not remain visible after submission');
      }
      if (completion.successText !== 'Capability complete') {
        failures.push('success state text is not exact');
      }
      report.interaction = {
        ...(report.interaction || {}),
        ...completion,
      };
      report.failures = [...new Set(failures)];
      report.status = report.failures.length ? 'failed' : 'passed';
      await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
    }

    process.stdout.write(
      `${JSON.stringify({ status: report.status, report: reportPath })}\n`,
    );
    process.exitCode = report.status === 'passed'
      ? 0
      : report.status === 'blocked'
        ? 2
        : 1;
  } catch (error) {
    const resolvedOutput = outputDir || resolve(process.cwd());
    await mkdir(resolvedOutput, { recursive: true });
    const report = {
      schemaVersion: 1,
      status: 'failed',
      error: `${error?.name || 'Error'}: ${error?.message || String(error)}`,
      failures: [],
    };
    const reportPath = join(resolvedOutput, 'browser-report.json');
    await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
    process.stdout.write(
      `${JSON.stringify({ status: report.status, report: reportPath })}\n`,
    );
    process.exitCode = 1;
  }
}

await main();
