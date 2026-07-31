#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import process from 'node:process';

const BASE_BROWSER_SCRIPT = new URL('./run_browser_capability.mjs', import.meta.url);

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

async function main() {
  let args;
  let outputDir;
  let report;
  try {
    args = parseArgs(process.argv.slice(2));
    outputDir = resolve(args.outputDir);
    await mkdir(outputDir, { recursive: true });
    const base = spawnSync(
      process.execPath,
      [BASE_BROWSER_SCRIPT.pathname, ...process.argv.slice(2)],
      { encoding: 'utf8', timeout: 60000, env: process.env },
    );
    if (base.error) throw base.error;
    const reportPath = join(outputDir, 'browser-report.json');
    report = JSON.parse(await readFile(reportPath, 'utf8'));
    if (report.status === 'passed' && base.status !== 0) {
      report.status = 'failed';
      report.failures = [...(report.failures || []), `base browser probe exited ${base.status}`];
      await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
    }
  } catch (error) {
    outputDir = resolve(args?.outputDir || process.cwd());
    await mkdir(outputDir, { recursive: true });
    report = {
      schemaVersion: 1,
      status: 'failed',
      error: `${error?.name || 'Error'}: ${error?.message || String(error)}`,
      failures: [],
    };
    await writeFile(join(outputDir, 'browser-report.json'), `${JSON.stringify(report, null, 2)}\n`);
  }

  process.stdout.write(`${JSON.stringify({ status: report.status, report: join(outputDir, 'browser-report.json') })}\n`);
  process.exitCode = report.status === 'passed' ? 0 : report.status === 'blocked' ? 2 : 1;
}

await main();
