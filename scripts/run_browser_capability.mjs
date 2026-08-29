#!/usr/bin/env node
import { spawn } from 'node:child_process';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join, resolve } from 'node:path';
import process from 'node:process';

const BASE_BROWSER_SCRIPT = fileURLToPath(
  new URL('./run_browser_capability_base.mjs', import.meta.url),
);
const CAPTURE_LIMIT = 64_000;
const DIAGNOSTIC_LIMIT = 2_000;
const STARTUP_MARKERS = [
  'chrome executable does not exist',
  'chrome or chromium is not installed',
  'chrome could not start',
  'chrome exited before devtools was ready',
  'chrome devtools did not become ready',
  'chrome exposed no debuggable page target',
  'devtools websocket failed to open',
  'devtools websocket timed out while opening',
  'chrome exposed no main frame',
];

class BrowserWrapperError extends Error {}

function parseOutputDir(argv) {
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key || value === undefined) {
      throw new BrowserWrapperError(`unknown or incomplete argument: ${key || '<missing>'}`);
    }
    if (key === '--output-dir') return value;
  }
  throw new BrowserWrapperError('--output-dir is required');
}

function appendBounded(current, chunk) {
  if (current.length >= CAPTURE_LIMIT) return current;
  const remaining = CAPTURE_LIMIT - current.length;
  return current + String(chunk || '').slice(0, remaining);
}

function boundedDiagnostic(value) {
  const text = String(value || '').trim();
  if (!text) return null;
  return text.length <= DIAGNOSTIC_LIMIT
    ? text
    : `${text.slice(0, DIAGNOSTIC_LIMIT)}…`;
}

function blockedPhase(report) {
  if (report?.status !== 'blocked') return null;
  const text = String(report.error || '').toLowerCase();
  return STARTUP_MARKERS.some((marker) => text.includes(marker))
    ? 'startup'
    : 'probe';
}

function terminalPhase(report) {
  if (report?.status === 'blocked') return blockedPhase(report);
  if (report?.status === 'failed') return 'contract';
  if (report?.status === 'passed') return 'complete';
  return 'wrapper';
}

async function runBaseProbe(argv, outputDir) {
  const reportPath = join(outputDir, 'browser-report.json');
  await rm(reportPath, { force: true });
  const startedAt = Date.now();
  return new Promise((resolvePromise, rejectPromise) => {
    let stdout = '';
    let stderr = '';
    const child = spawn(
      process.execPath,
      [BASE_BROWSER_SCRIPT, ...argv],
      {
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
    child.once('error', rejectPromise);
    child.once('close', async (status, signal) => {
      try {
        const report = JSON.parse(await readFile(reportPath, 'utf8'));
        resolvePromise({
          status,
          signal,
          stdout,
          stderr,
          report,
          elapsedMs: Math.max(0, Date.now() - startedAt),
        });
      } catch (error) {
        rejectPromise(error);
      }
    });
  });
}

function normalizeExit(report, attempt) {
  if (report.status !== 'passed' || attempt.status === 0) return report;
  const failures = [
    ...(Array.isArray(report.failures) ? report.failures : []),
    `base browser probe exited ${attempt.status ?? 'without a status'}${attempt.signal ? ` (${attempt.signal})` : ''}`,
  ];
  const stdout = boundedDiagnostic(attempt.stdout);
  const stderr = boundedDiagnostic(attempt.stderr);
  if (stdout) failures.push(`base browser stdout: ${stdout}`);
  if (stderr) failures.push(`base browser stderr: ${stderr}`);
  return {
    ...report,
    status: 'failed',
    failures,
  };
}

function decorateReport(report, attempt, startupRetry) {
  const normalized = normalizeExit(report, attempt);
  const phase = terminalPhase(normalized);
  const observationMs = Number(normalized?.network?.observationMs);
  const timing = {
    attemptMs: attempt.elapsedMs,
    startupMs: phase === 'startup' ? attempt.elapsedMs : null,
    observationMs: Number.isFinite(observationMs) && observationMs >= 0
      ? observationMs
      : 0,
  };
  return {
    ...normalized,
    phase,
    timing,
    startupRetry,
  };
}

async function persistReport(reportPath, report) {
  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
}

async function main() {
  let outputDir;
  let reportPath;
  let report;
  try {
    const argv = process.argv.slice(2);
    outputDir = resolve(parseOutputDir(argv));
    reportPath = join(outputDir, 'browser-report.json');
    await mkdir(outputDir, { recursive: true });

    const first = await runBaseProbe(argv, outputDir);
    const firstReport = normalizeExit(first.report, first);
    const firstPhase = terminalPhase(firstReport);
    let finalAttempt = first;
    let startupRetry = {
      attempted: false,
      attempts: 1,
      firstAttempt: null,
    };

    if (firstReport.status === 'blocked' && firstPhase === 'startup') {
      startupRetry = {
        attempted: true,
        attempts: 2,
        firstAttempt: {
          status: firstReport.status,
          phase: firstPhase,
          error: firstReport.error || null,
          timing: {
            attemptMs: first.elapsedMs,
            startupMs: first.elapsedMs,
            observationMs: 0,
          },
        },
      };
      finalAttempt = await runBaseProbe(argv, outputDir);
    }

    report = decorateReport(finalAttempt.report, finalAttempt, startupRetry);
    await persistReport(reportPath, report);
  } catch (error) {
    outputDir = resolve(outputDir || process.cwd());
    reportPath = join(outputDir, 'browser-report.json');
    report = {
      schemaVersion: 1,
      status: 'failed',
      phase: 'wrapper',
      timing: {
        attemptMs: 0,
        startupMs: null,
        observationMs: 0,
      },
      startupRetry: {
        attempted: false,
        attempts: 0,
        firstAttempt: null,
      },
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
