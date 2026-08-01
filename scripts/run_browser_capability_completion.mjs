#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join, resolve } from 'node:path';
import process from 'node:process';

const BASE_BROWSER_SCRIPT = fileURLToPath(
  new URL('./run_browser_capability.mjs', import.meta.url),
);
const DIAGNOSTIC_LIMIT = 2000;

class CompletionProbeError extends Error {}

function parseArgs(argv) {
  const args = { outputDir: null };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (key === '--output-dir') args.outputDir = value;
    else if (['--root', '--entrypoint', '--width', '--height'].includes(key)) {
      // The base probe validates these values.
    } else {
      throw new CompletionProbeError(`unknown or incomplete argument: ${key}`);
    }
    index += 1;
  }
  if (!args.outputDir) throw new CompletionProbeError('--output-dir is required');
  return args;
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
    const base = spawnSync(
      process.execPath,
      [BASE_BROWSER_SCRIPT, ...process.argv.slice(2)],
      { encoding: 'utf8', timeout: 60000, env: process.env },
    );
    if (base.error) throw base.error;
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
      status: 'failed',
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
