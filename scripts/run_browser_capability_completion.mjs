#!/usr/bin/env node
import { spawn } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join, resolve } from 'node:path';
import process from 'node:process';

const BASE_BROWSER_SCRIPT = fileURLToPath(
  new URL('./run_browser_capability.mjs', import.meta.url),
);
const DIAGNOSTIC_LIMIT = 2000;
const CAPTURE_LIMIT = 64_000;
const DEFAULT_BASE_TIMEOUT_MS = 60_000;
const TERMINATION_GRACE_MS = 1_000;

class CompletionProbeError extends Error {}
class CompletionProbeBlockedError extends CompletionProbeError {}

function parseArgs(argv) {
  const args = { outputDir: null };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (key === '--output-dir') args.outputDir = value;
    else if (['--root', '--entrypoint', '--width', '--height', '--forbidden-text'].includes(key)) {
      // The base probe validates these values.
    } else {
      throw new CompletionProbeError(`unknown or incomplete argument: ${key}`);
    }
    index += 1;
  }
  if (!args.outputDir) throw new CompletionProbeError('--output-dir is required');
  return args;
}

function baseTimeoutMs() {
  const raw = process.env.DESIGN_STUDIO_BROWSER_COMPLETION_TIMEOUT_MS;
  if (raw === undefined || raw === '') return DEFAULT_BASE_TIMEOUT_MS;
  const parsed = Number(raw);
  if (!Number.isInteger(parsed) || parsed < 100 || parsed > DEFAULT_BASE_TIMEOUT_MS) {
    throw new CompletionProbeError(
      'DESIGN_STUDIO_BROWSER_COMPLETION_TIMEOUT_MS must be an integer from 100 to 60000',
    );
  }
  return parsed;
}

function appendBounded(current, chunk) {
  if (current.length >= CAPTURE_LIMIT) return current;
  const remaining = CAPTURE_LIMIT - current.length;
  const text = String(chunk || '');
  return current + text.slice(0, remaining);
}

function terminateProcessTree(child, signal) {
  if (!child?.pid || child.exitCode !== null || child.signalCode !== null) return;
  try {
    if (process.platform === 'win32') child.kill(signal);
    else process.kill(-child.pid, signal);
  } catch (error) {
    if (error?.code !== 'ESRCH') {
      try {
        child.kill(signal);
      } catch (fallbackError) {
        if (fallbackError?.code !== 'ESRCH') throw fallbackError;
      }
    }
  }
}

async function runBaseProbe(argv) {
  const timeoutMs = baseTimeoutMs();
  return new Promise((resolvePromise, rejectPromise) => {
    let settled = false;
    let timedOut = false;
    let forceTimer = null;
    let stdout = '';
    let stderr = '';
    const child = spawn(
      process.execPath,
      [BASE_BROWSER_SCRIPT, ...argv],
      {
        detached: process.platform !== 'win32',
        env: process.env,
        stdio: ['ignore', 'pipe', 'pipe'],
      },
    );

    child.stdout?.setEncoding('utf8');
    child.stderr?.setEncoding('utf8');
    child.stdout?.on('data', (chunk) => {
      stdout = appendBounded(stdout, chunk);
    });
    child.stderr?.on('data', (chunk) => {
      stderr = appendBounded(stderr, chunk);
    });

    const finish = (callback) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutTimer);
      if (forceTimer) clearTimeout(forceTimer);
      callback();
    };

    const timeoutTimer = setTimeout(() => {
      timedOut = true;
      try {
        terminateProcessTree(child, 'SIGTERM');
      } catch (error) {
        finish(() => rejectPromise(error));
        return;
      }
      forceTimer = setTimeout(() => {
        try {
          terminateProcessTree(child, 'SIGKILL');
        } catch (error) {
          finish(() => rejectPromise(error));
        }
      }, TERMINATION_GRACE_MS);
      forceTimer.unref?.();
    }, timeoutMs);
    timeoutTimer.unref?.();

    child.once('error', (error) => {
      finish(() => rejectPromise(error));
    });
    child.once('close', (status, signal) => {
      if (timedOut) {
        finish(() => rejectPromise(new CompletionProbeBlockedError(
          `base browser probe timed out after ${timeoutMs} ms`,
        )));
        return;
      }
      finish(() => resolvePromise({ status, signal, stdout, stderr }));
    });
  });
}

function boundedDiagnostic(value) {
  const text = String(value || '').trim();
  if (!text) return null;
  return text.length <= DIAGNOSTIC_LIMIT
    ? text
    : `${text.slice(0, DIAGNOSTIC_LIMIT)}…`;
}

async function persistReport(reportPath, report) {
  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
}

async function main() {
  let args;
  let outputDir;
  let report;
  let reportPath;
  try {
    args = parseArgs(process.argv.slice(2));
    outputDir = resolve(args.outputDir);
    reportPath = join(outputDir, 'browser-report.json');
    await mkdir(outputDir, { recursive: true });
    const base = await runBaseProbe(process.argv.slice(2));
    report = JSON.parse(await readFile(reportPath, 'utf8'));
    if (report.status === 'passed' && base.status !== 0) {
      const failures = [
        ...(report.failures || []),
        `base browser probe exited ${base.status ?? 'without a status'}${base.signal ? ` (${base.signal})` : ''}`,
      ];
      const stdout = boundedDiagnostic(base.stdout);
      const stderr = boundedDiagnostic(base.stderr);
      if (stdout) failures.push(`base browser stdout: ${stdout}`);
      if (stderr) failures.push(`base browser stderr: ${stderr}`);
      report.status = 'failed';
      report.failures = failures;
      await persistReport(reportPath, report);
    }
  } catch (error) {
    outputDir = resolve(args?.outputDir || process.cwd());
    reportPath = join(outputDir, 'browser-report.json');
    report = {
      schemaVersion: 1,
      status: error instanceof CompletionProbeBlockedError ? 'blocked' : 'failed',
      error: `${error?.name || 'Error'}: ${error?.message || String(error)}`,
      failures: [],
    };
    try {
      await mkdir(outputDir, { recursive: true });
      await persistReport(reportPath, report);
    } catch (persistError) {
      process.stderr.write(
        `failed to persist failure report: ${persistError?.message || String(persistError)}\n`,
      );
    }
  }

  process.stdout.write(`${JSON.stringify({ status: report.status, report: reportPath })}\n`);
  process.exitCode = report.status === 'passed' ? 0 : report.status === 'blocked' ? 2 : 1;
}

await main();
