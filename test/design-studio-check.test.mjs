import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { scanProject } from '../scripts/design-studio-check.mjs';

function fixture(files) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'design-studio-check-'));
  for (const [relative, content] of Object.entries(files)) {
    const destination = path.join(root, relative);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.writeFileSync(destination, content);
  }
  return root;
}

function openIds(report) {
  return report.findings.filter((finding) => finding.status === 'open').map((finding) => finding.id);
}

test('finds blocking accessibility and placeholder-link defects', () => {
  const root = fixture({
    'index.html': `<!doctype html>
<html lang="en">
<head><meta name="viewport" content="width=device-width"><title>Test</title></head>
<body>
  <a href="#">Continue</a>
  <img src="hero.png">
  <div role="button">Open</div>
</body>
</html>`
  });

  const report = scanProject(root, { mode: 'operate' });
  assert.equal(report.summary.blocker, 3);
  assert.deepEqual(new Set(openIds(report)), new Set([
    'placeholder-link',
    'image-alt-missing',
    'fake-button-keyboard-missing'
  ]));
});

test('finds motion and focus quality gaps at project level', () => {
  const root = fixture({
    'index.html': `<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width"><title>Test</title><link rel="stylesheet" href="app.css"></head><body><button id="go">Go</button><script>go.addEventListener('click', () => {})</script></body></html>`,
    'app.css': `.panel { transition: opacity 180ms ease; }`
  });

  const report = scanProject(root, { mode: 'persuade' });
  assert.equal(report.summary.blocker, 0);
  assert.ok(openIds(report).includes('reduced-motion-missing'));
  assert.ok(openIds(report).includes('focus-style-missing'));
});

test('accepts an accessible minimal surface', () => {
  const root = fixture({
    'index.html': `<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Test</title><link rel="stylesheet" href="app.css"></head><body><button id="go">Go</button><script>go.addEventListener('click', () => {})</script></body></html>`,
    'app.css': `button:focus-visible { outline: 3px solid currentColor; outline-offset: 3px; }`
  });

  const report = scanProject(root, { mode: 'operate' });
  assert.equal(report.summary.blocker, 0);
  assert.equal(report.summary.quality, 0);
});

test('records ignored findings instead of deleting them', () => {
  const root = fixture({
    '.design-studio/check.json': JSON.stringify({ ignoreRules: ['transition-all'] }),
    'index.html': `<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width"><title>Test</title><link rel="stylesheet" href="app.css"></head><body></body></html>`,
    'app.css': `.thing { transition: all 200ms ease; }
@media (prefers-reduced-motion: reduce) { .thing { transition: none; } }`
  });

  const report = scanProject(root, { mode: 'read' });
  const finding = report.findings.find((item) => item.id === 'transition-all');
  assert.equal(finding.status, 'ignored');
  assert.equal(report.summary.ignored, 1);
});

test('rejects an unknown surface mode', () => {
  const root = fixture({ 'index.html': '<!doctype html>' });
  assert.throws(() => scanProject(root, { mode: 'dashboard' }), /Invalid mode/);
});
