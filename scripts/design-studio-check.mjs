#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const VERSION = 1;
const TEXT_EXTENSIONS = new Set([
  '.html', '.htm', '.css', '.scss', '.sass', '.less',
  '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue', '.svelte'
]);
const DEFAULT_IGNORED_DIRS = new Set([
  '.git', 'node_modules', 'dist', 'build', 'coverage', '.next', '.nuxt', '.svelte-kit'
]);
const VALID_MODES = new Set(['persuade', 'operate', 'read', 'experience']);

function toPosix(value) {
  return value.split(path.sep).join('/');
}

function globToRegExp(glob) {
  const escaped = glob
    .replace(/[.+^${}()|[\]\\]/g, '\\$&')
    .replace(/\*\*/g, '::DOUBLE_STAR::')
    .replace(/\*/g, '[^/]*')
    .replace(/::DOUBLE_STAR::/g, '.*')
    .replace(/\?/g, '.');
  return new RegExp(`^${escaped}$`);
}

function matchesAnyGlob(file, patterns) {
  return patterns.some((pattern) => globToRegExp(toPosix(pattern)).test(toPosix(file)));
}

function walk(entryPath, rootPath, files = []) {
  const stat = fs.statSync(entryPath);
  if (stat.isFile()) {
    if (TEXT_EXTENSIONS.has(path.extname(entryPath).toLowerCase())) files.push(entryPath);
    return files;
  }

  for (const entry of fs.readdirSync(entryPath, { withFileTypes: true })) {
    if (entry.isDirectory() && DEFAULT_IGNORED_DIRS.has(entry.name)) continue;
    const absolute = path.join(entryPath, entry.name);
    if (entry.isDirectory()) walk(absolute, rootPath, files);
    else if (TEXT_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) files.push(absolute);
  }
  return files;
}

function lineNumberAt(content, index) {
  return content.slice(0, Math.max(0, index)).split('\n').length;
}

function excerptAt(content, index, length = 100) {
  const lineStart = content.lastIndexOf('\n', index) + 1;
  const lineEndRaw = content.indexOf('\n', index);
  const lineEnd = lineEndRaw === -1 ? content.length : lineEndRaw;
  return content.slice(lineStart, Math.min(lineEnd, lineStart + length)).trim();
}

function hasNearbyIgnore(content, index, ruleId) {
  const before = content.slice(0, index).split('\n').slice(-3).join('\n');
  const current = excerptAt(content, index, 300);
  const marker = `design-studio-ignore ${ruleId}`;
  return before.includes(marker) || current.includes(marker);
}

function loadConfig(root) {
  const configPath = path.join(root, '.design-studio', 'check.json');
  if (!fs.existsSync(configPath)) return { ignoreRules: [], ignoreFiles: [] };

  try {
    const parsed = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    return {
      ignoreRules: Array.isArray(parsed.ignoreRules) ? parsed.ignoreRules : [],
      ignoreFiles: Array.isArray(parsed.ignoreFiles) ? parsed.ignoreFiles : []
    };
  } catch (error) {
    return {
      ignoreRules: [],
      ignoreFiles: [],
      configError: `Could not parse ${toPosix(path.relative(root, configPath))}: ${error.message}`
    };
  }
}

function scanRegex({ content, relativeFile, regex, id, severity, message, findings, config, evidence }) {
  regex.lastIndex = 0;
  for (const match of content.matchAll(regex)) {
    const index = match.index ?? 0;
    const ignored = config.ignoreRules.includes(id)
      || matchesAnyGlob(relativeFile, config.ignoreFiles)
      || hasNearbyIgnore(content, index, id);
    findings.push({
      id,
      severity,
      file: relativeFile,
      line: lineNumberAt(content, index),
      message,
      evidence: evidence ? evidence(match) : excerptAt(content, index),
      status: ignored ? 'ignored' : 'open'
    });
  }
}

function scanFile(file, root, findings, config, projectSignals) {
  const relativeFile = toPosix(path.relative(root, file));
  if (matchesAnyGlob(relativeFile, config.ignoreFiles)) return;

  const content = fs.readFileSync(file, 'utf8');
  const ext = path.extname(file).toLowerCase();
  const lower = content.toLowerCase();

  if (['.html', '.htm'].includes(ext)) {
    if (!/<html\b[^>]*\blang\s*=/.test(content)) {
      findings.push({
        id: 'document-language-missing', severity: 'quality', file: relativeFile, line: 1,
        message: 'The document does not declare its language.', evidence: '<html> has no lang attribute', status: 'open'
      });
    }
    if (!/<meta\b[^>]*name=["']viewport["'][^>]*>/i.test(content)) {
      findings.push({
        id: 'viewport-meta-missing', severity: 'blocker', file: relativeFile, line: 1,
        message: 'The document has no responsive viewport declaration.', evidence: 'Missing <meta name="viewport">', status: 'open'
      });
    }
    if (!/<title>[^<]+<\/title>/i.test(content)) {
      findings.push({
        id: 'document-title-missing', severity: 'quality', file: relativeFile, line: 1,
        message: 'The document has no meaningful title.', evidence: 'Missing or empty <title>', status: 'open'
      });
    }

    scanRegex({
      content, relativeFile, findings, config,
      regex: /<img\b(?![^>]*\balt\s*=)[^>]*>/gi,
      id: 'image-alt-missing', severity: 'blocker',
      message: 'An image has no alt attribute.'
    });
    scanRegex({
      content, relativeFile, findings, config,
      regex: /\bhref\s*=\s*["'](?:#|javascript:\s*void\s*\(\s*0\s*\))["']/gi,
      id: 'placeholder-link', severity: 'blocker',
      message: 'A functional link uses a placeholder destination.'
    });
    scanRegex({
      content, relativeFile, findings, config,
      regex: /<a\b(?=[^>]*target=["']_blank["'])(?![^>]*rel=["'][^"']*(?:noopener|noreferrer))[^>]*>/gi,
      id: 'blank-target-rel-missing', severity: 'quality',
      message: 'A new-tab link is missing noopener or noreferrer.'
    });
    scanRegex({
      content, relativeFile, findings, config,
      regex: /<(?:div|span)\b(?=[^>]*role=["']button["'])(?![^>]*tabindex=)[^>]*>/gi,
      id: 'fake-button-keyboard-missing', severity: 'blocker',
      message: 'A non-button control with role="button" is not keyboard focusable.'
    });

    const inlineStyleCount = (content.match(/\sstyle\s*=\s*["']/gi) || []).length;
    if (inlineStyleCount > 5) {
      findings.push({
        id: 'inline-style-sprawl', severity: 'polish', file: relativeFile, line: 1,
        message: 'The surface contains many inline style declarations, making visual rules harder to maintain.',
        evidence: `${inlineStyleCount} inline style attributes`, status: 'open'
      });
    }
  }

  if (['.jsx', '.tsx', '.vue', '.svelte'].includes(ext)) {
    scanRegex({
      content, relativeFile, findings, config,
      regex: /<(?:div|span)\b(?=[^>]*(?:onClick|@click|on:click)=)(?![^>]*(?:role=["']button["']|tabIndex=|tabindex=))[^>]*>/g,
      id: 'clickable-non-control', severity: 'quality',
      message: 'A non-control element handles clicks without an explicit keyboard/control contract.'
    });
    scanRegex({
      content, relativeFile, findings, config,
      regex: /<img\b(?![^>]*\balt=)[^>]*>/g,
      id: 'image-alt-missing', severity: 'blocker',
      message: 'An image has no alt property.'
    });
  }

  if (['.css', '.scss', '.sass', '.less'].includes(ext)) {
    projectSignals.hasCss = true;
    if (/\b(?:animation|transition)\s*:/.test(content)) projectSignals.hasMotion = true;
    if (/@media\s*\(prefers-reduced-motion\s*:\s*reduce\)/i.test(content)) projectSignals.hasReducedMotion = true;
    if (/:focus(?:-visible|-within)?\b/i.test(content)) projectSignals.hasFocusStyle = true;

    scanRegex({
      content, relativeFile, findings, config,
      regex: /\btransition\s*:\s*all\b[^;]*/gi,
      id: 'transition-all', severity: 'quality',
      message: 'transition: all can animate layout or state changes unintentionally.'
    });
    scanRegex({
      content, relativeFile, findings, config,
      regex: /\boutline\s*:\s*(?:none|0(?:\s+none)?)\s*;?/gi,
      id: 'focus-outline-removed', severity: 'blocker',
      message: 'A focus outline is removed. Provide a visible focus-visible replacement.'
    });
    scanRegex({
      content, relativeFile, findings, config,
      regex: /(?:-webkit-)?background-clip\s*:\s*text|\bcolor\s*:\s*transparent\s*;[^}]{0,160}(?:linear|radial)-gradient/gi,
      id: 'decorative-gradient-text', severity: 'quality',
      message: 'Gradient text is a common decorative reflex; keep it only when the committed visual world requires it.'
    });
    scanRegex({
      content, relativeFile, findings, config,
      regex: /\b(?:filter\s*:\s*drop-shadow|box-shadow\s*:\s*0\s+0\s+\d+px\s+[^;]+)/gi,
      id: 'zero-offset-glow', severity: 'polish',
      message: 'A zero-offset glow is being used as generic depth or emphasis.'
    });
    scanRegex({
      content, relativeFile, findings, config,
      regex: /\.card[\w-]*\s*\{[^}]{0,500}\bborder-radius\s*:[^;}]+;[^}]{0,300}\bbox-shadow\s*:/gis,
      id: 'rounded-shadow-card-reflex', severity: 'polish',
      message: 'A generic rounded-and-shadowed card pattern appears in the surface.'
    });
  }

  if (['.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue', '.svelte', '.html', '.htm'].includes(ext)) {
    if (/(?:addEventListener\s*\(\s*["']click|onClick\s*=|@click\s*=|on:click\s*=)/.test(content)) {
      projectSignals.hasInteractivity = true;
    }
    scanRegex({
      content, relativeFile, findings, config,
      regex: /<(?:button|a)\b[^>]*>[\s\S]{0,120}?[\u{1F300}-\u{1FAFF}][\s\S]{0,120}?<\/(?:button|a)>/gu,
      id: 'emoji-as-control-icon', severity: 'quality',
      message: 'An emoji is used inside a control. Use an intentional icon or text label unless the brief requires emoji.'
    });
  }

  if (/lorem\s+ipsum|your\s+(?:company|product|headline)|example\.com/i.test(lower)) {
    scanRegex({
      content, relativeFile, findings, config,
      regex: /lorem\s+ipsum|your\s+(?:company|product|headline)|example\.com/gi,
      id: 'placeholder-content', severity: 'quality',
      message: 'Placeholder content remains in a user-facing surface.'
    });
  }
}

function applyProjectRules(findings, config, projectSignals, root) {
  const projectFile = '(project)';
  if (config.configError) {
    findings.push({
      id: 'invalid-check-config', severity: 'blocker', file: '.design-studio/check.json', line: 1,
      message: config.configError, evidence: config.configError, status: 'open'
    });
  }

  if (projectSignals.hasMotion && !projectSignals.hasReducedMotion) {
    const ignored = config.ignoreRules.includes('reduced-motion-missing');
    findings.push({
      id: 'reduced-motion-missing', severity: 'quality', file: projectFile, line: 1,
      message: 'Motion is present without a prefers-reduced-motion path.',
      evidence: 'Animation or transition declarations found; no reduced-motion media query found.',
      status: ignored ? 'ignored' : 'open'
    });
  }

  if (projectSignals.hasInteractivity && projectSignals.hasCss && !projectSignals.hasFocusStyle) {
    const ignored = config.ignoreRules.includes('focus-style-missing');
    findings.push({
      id: 'focus-style-missing', severity: 'quality', file: projectFile, line: 1,
      message: 'Interactive controls are present but no authored focus style was found.',
      evidence: 'Click handlers found; no :focus, :focus-visible, or :focus-within selector found.',
      status: ignored ? 'ignored' : 'open'
    });
  }
}

function summarize(findings) {
  const summary = { blocker: 0, quality: 0, polish: 0, ignored: 0 };
  for (const finding of findings) {
    if (finding.status === 'ignored') summary.ignored += 1;
    else summary[finding.severity] += 1;
  }
  return summary;
}

export function scanProject(target, options = {}) {
  const absoluteTarget = path.resolve(target);
  if (!fs.existsSync(absoluteTarget)) {
    throw new Error(`Target does not exist: ${absoluteTarget}`);
  }

  const root = fs.statSync(absoluteTarget).isDirectory() ? absoluteTarget : path.dirname(absoluteTarget);
  const mode = options.mode || 'persuade';
  if (!VALID_MODES.has(mode)) throw new Error(`Invalid mode: ${mode}`);

  const config = loadConfig(root);
  const files = walk(absoluteTarget, root);
  const findings = [];
  const projectSignals = {
    hasCss: false,
    hasMotion: false,
    hasReducedMotion: false,
    hasFocusStyle: false,
    hasInteractivity: false
  };

  if (files.length === 0) {
    findings.push({
      id: 'no-scannable-files', severity: 'blocker', file: '(project)', line: 1,
      message: 'No supported frontend source files were found.', evidence: toPosix(absoluteTarget), status: 'open'
    });
  } else {
    for (const file of files) scanFile(file, root, findings, config, projectSignals);
    applyProjectRules(findings, config, projectSignals, root);
  }

  findings.sort((a, b) => {
    const order = { blocker: 0, quality: 1, polish: 2 };
    return (a.status === 'ignored') - (b.status === 'ignored')
      || order[a.severity] - order[b.severity]
      || a.file.localeCompare(b.file)
      || a.line - b.line
      || a.id.localeCompare(b.id);
  });

  return {
    version: VERSION,
    mode,
    target: toPosix(path.relative(process.cwd(), absoluteTarget) || '.'),
    scannedFiles: files.length,
    summary: summarize(findings),
    findings
  };
}

function parseArgs(argv) {
  const args = { target: null, json: null, mode: 'persuade', strict: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--json') args.json = argv[++i];
    else if (arg === '--mode') args.mode = argv[++i];
    else if (arg === '--strict') args.strict = true;
    else if (arg === '--help' || arg === '-h') args.help = true;
    else if (!args.target) args.target = arg;
    else throw new Error(`Unexpected argument: ${arg}`);
  }
  return args;
}

function printHelp() {
  console.log(`Design Studio deterministic preflight\n\nUsage:\n  node scripts/design-studio-check.mjs <target> [--mode persuade|operate|read|experience] [--json <path>] [--strict]\n\nExit codes:\n  0  no open blockers (and no quality findings in strict mode)\n  1  blocking findings, or quality findings in strict mode\n  2  invalid invocation or unreadable target`);
}

function printReport(report) {
  const { blocker, quality, polish, ignored } = report.summary;
  console.log(`Design Studio preflight: ${report.scannedFiles} files, ${blocker} blocker, ${quality} quality, ${polish} polish, ${ignored} ignored`);
  for (const finding of report.findings.filter((item) => item.status === 'open')) {
    console.log(`${finding.severity.toUpperCase()} ${finding.id} ${finding.file}:${finding.line} — ${finding.message}`);
  }
}

async function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    if (args.help || !args.target) {
      printHelp();
      process.exitCode = args.help ? 0 : 2;
      return;
    }

    const report = scanProject(args.target, { mode: args.mode });
    printReport(report);

    if (args.json) {
      const output = path.resolve(args.json);
      fs.mkdirSync(path.dirname(output), { recursive: true });
      fs.writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
    }

    const failed = report.summary.blocker > 0 || (args.strict && report.summary.quality > 0);
    process.exitCode = failed ? 1 : 0;
  } catch (error) {
    console.error(`design-studio-check: ${error.message}`);
    process.exitCode = 2;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  await main();
}
