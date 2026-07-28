#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { scanProject } from './design-studio-check.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const errors = [];
const warnings = [];

function read(relative) {
  const absolute = path.join(root, relative);
  if (!fs.existsSync(absolute)) {
    errors.push(`Missing required file: ${relative}`);
    return '';
  }
  return fs.readFileSync(absolute, 'utf8');
}

function requireText(relative, text, description = text) {
  const content = read(relative);
  if (!content.includes(text)) errors.push(`${relative} is missing ${description}`);
}

const requiredFiles = [
  'commands/init.md',
  'commands/create.md',
  'commands/review.md',
  'skills/design-studio/SKILL.md',
  'skills/design-studio/workflow.yaml',
  'skills/design-studio/agents/design-agent.md',
  'skills/design-studio/agents/evaluator.md',
  'skills/design-studio/references/context.md',
  'skills/design-studio/references/modes.md',
  'skills/design-studio/references/preflight.md',
  'skills/design-studio/assets/context/PRODUCT.md.template',
  'skills/design-studio/assets/context/DESIGN.md.template',
  'skills/design-studio/assets/context/surface.md.template',
  'scripts/design-studio-check.mjs',
  'skills/design-studio/evals/evals.json',
  'README.md',
  'docs/index.html'
];
requiredFiles.forEach(read);

let plugin;
try {
  plugin = JSON.parse(read('.claude-plugin/plugin.json'));
} catch (error) {
  errors.push(`.claude-plugin/plugin.json is invalid JSON: ${error.message}`);
  plugin = { version: '(invalid)' };
}

const skill = read('skills/design-studio/SKILL.md');
const skillVersion = skill.match(/^version:\s*["']?([^\n"']+)/m)?.[1]?.trim();
const workflow = read('skills/design-studio/workflow.yaml');
const workflowVersion = workflow.match(/^version:\s*["']?([^\n"']+)/m)?.[1]?.trim();

if (!skillVersion) errors.push('SKILL.md has no version in frontmatter.');
if (!workflowVersion) errors.push('workflow.yaml has no top-level version.');
if (plugin.version !== skillVersion || plugin.version !== workflowVersion) {
  errors.push(`Version drift: plugin=${plugin.version}, skill=${skillVersion}, workflow=${workflowVersion}`);
}

for (const mode of ['persuade', 'operate', 'read', 'experience']) {
  if (!workflow.includes(`${mode}:`)) errors.push(`workflow.yaml has no ${mode} mode.`);
}
for (const profile of ['component', 'standard', 'ambitious']) {
  if (!workflow.includes(`${profile}:`)) errors.push(`workflow.yaml has no ${profile} profile.`);
}
for (const decision of ['REFINE', 'PIVOT', 'SHIP', 'HOLD']) {
  if (!workflow.includes(decision)) errors.push(`workflow.yaml has no ${decision} decision contract.`);
}

if (/maxIterations\s*:\s*(?:8|9|1\d)/.test(workflow)) {
  errors.push('workflow.yaml still contains an unbounded legacy maxIterations default.');
}
if (/budget[^\n]{0,100}(?:ship|SHIP)|(?:ship|SHIP)[^\n]{0,100}budget/.test(workflow)
  && !/budget exhausted[^\n]{0,100}HOLD|HOLD[^\n]{0,100}budget exhausted/i.test(workflow)) {
  warnings.push('Review the workflow wording: budget exhaustion must not imply SHIP.');
}

for (const command of ['init', 'create', 'review']) {
  requireText('README.md', `/design-studio:${command}`, `the ${command} command`);
  requireText('docs/index.html', `/design-studio:${command}`, `the ${command} command`);
}

requireText('skills/design-studio/SKILL.md', '.design-studio/PRODUCT.md', 'durable product context');
requireText('skills/design-studio/SKILL.md', 'HOLD', 'the HOLD state');
requireText('skills/design-studio/SKILL.md', 'deterministic preflight', 'deterministic preflight routing');
requireText('skills/design-studio/agents/evaluator.md', 'never receives source code', 'the evaluator isolation rule');
requireText('skills/design-studio/agents/design-agent.md', 'never receives source code', 'the design-agent isolation rule');

try {
  const evals = JSON.parse(read('skills/design-studio/evals/evals.json'));
  if (!Array.isArray(evals.evals) || evals.evals.length < 8) {
    errors.push('evals.json must contain at least eight routing/behavior evals.');
  }
  const serialized = JSON.stringify(evals);
  for (const expected of ['operate', 'HOLD', 'preflight', 'PRODUCT.md']) {
    if (!serialized.includes(expected)) errors.push(`evals.json does not exercise ${expected}.`);
  }
} catch (error) {
  errors.push(`skills/design-studio/evals/evals.json is invalid JSON: ${error.message}`);
}

try {
  const docsReport = scanProject(path.join(root, 'docs', 'index.html'), { mode: 'persuade' });
  if (docsReport.summary.blocker > 0) {
    for (const finding of docsReport.findings.filter((item) => item.status === 'open' && item.severity === 'blocker')) {
      errors.push(`docs preflight: ${finding.id} at ${finding.file}:${finding.line}`);
    }
  }
  if (docsReport.summary.quality > 0) {
    warnings.push(`docs preflight has ${docsReport.summary.quality} open quality finding(s).`);
  }
} catch (error) {
  errors.push(`Could not preflight docs/index.html: ${error.message}`);
}

for (const warning of warnings) console.warn(`WARN ${warning}`);
for (const error of errors) console.error(`ERROR ${error}`);

if (errors.length > 0) {
  console.error(`\nDesign Studio package validation failed with ${errors.length} error(s).`);
  process.exitCode = 1;
} else {
  console.log(`Design Studio package validation passed${warnings.length ? ` with ${warnings.length} warning(s)` : ''}.`);
}
