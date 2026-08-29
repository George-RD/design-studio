import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

import {
  MechanicalInputError,
  evaluateMechanicalSnapshot,
} from '../skills/design-studio/runtime/mechanical/index.mjs';

function cleanSource(overrides = {}) {
  return {
    target: 'site source',
    completed: true,
    pageTitle: 'Example',
    language: 'en',
    headingOrderValid: true,
    primaryHeadingCount: 1,
    motionPresent: true,
    reducedMotionHandled: true,
    semanticControlFailures: [],
    accessibleNameFailures: [],
    altTextFailures: [],
    landmarkFailures: [],
    focusVisibilityFailures: [],
    placeholderLinkFailures: [],
    debugControlFailures: [],
    ...overrides,
  };
}

function cleanBrowser(target, width, height, overrides = {}) {
  return {
    target,
    completed: true,
    requestedViewport: { width, height },
    actualViewport: { width, height },
    scrollWidth: width,
    clientWidth: width,
    motionPresent: true,
    reducedMotionVerified: true,
    contrastFailures: [],
    clippedContentFailures: [],
    keyboardFailures: [],
    focusFailures: [],
    touchTargetFailures: [],
    resourceFailures: [],
    fatalConsoleErrors: [],
    ...overrides,
  };
}

function cleanInput(overrides = {}) {
  return {
    schemaVersion: 1,
    generatedAt: '2026-08-29T08:00:00Z',
    source: cleanSource(),
    browser: [
      cleanBrowser('1440x900', 1440, 900),
      cleanBrowser('390x844', 390, 844),
    ],
    waivers: [],
    ...overrides,
  };
}

test('produces a stable local current snapshot and applies only exact waivers', () => {
  const input = cleanInput({
    source: cleanSource({ pageTitle: '', language: '', primaryHeadingCount: 2 }),
    browser: [
      cleanBrowser('1440x900', 1440, 900, { scrollWidth: 1470 }),
      cleanBrowser('390x844', 390, 844, {
        touchTargetFailures: [
          {
            location: '#menu',
            value: '32x32',
            evidence: 'Menu target is 32x32 CSS pixels.',
          },
        ],
      }),
    ],
    waivers: [
      {
        ruleId: 'touch-target-size',
        target: '390x844',
        location: '#menu',
        value: '32x32',
        authority: 'surface-brief.md#compact-menu',
        reason: 'Pinned compact control is paired with an equivalent full-size action.',
      },
    ],
  });

  const first = evaluateMechanicalSnapshot(input);
  const second = evaluateMechanicalSnapshot({
    ...input,
    generatedAt: '2026-08-29T08:05:00Z',
  });

  assert.equal(first.detector, 'design-studio');
  assert.equal(first.snapshotId, second.snapshotId);
  assert.deepEqual(first.passes, [
    { target: 'site source', kind: 'source', completed: true },
    { target: '1440x900', kind: 'browser', completed: true },
    { target: '390x844', kind: 'browser', completed: true },
  ]);

  const rules = new Set(first.findings.map((finding) => finding.ruleId));
  assert.deepEqual(
    rules,
    new Set([
      'document-title',
      'document-language',
      'primary-heading-count',
      'horizontal-overflow',
      'touch-target-size',
    ]),
  );
  assert.ok(first.findings.every((finding) => finding.signature.startsWith('sha256:')));

  const waived = first.findings.find((finding) => finding.ruleId === 'touch-target-size');
  assert.equal(waived.status, 'waived');
  assert.equal(waived.authority, 'surface-brief.md#compact-menu');
  assert.equal(waived.reason, 'Pinned compact control is paired with an equivalent full-size action.');

  const overflow = first.findings.find((finding) => finding.ruleId === 'horizontal-overflow');
  assert.equal(overflow.status, 'open');
  assert.equal(overflow.authority, null);
});

test('a new snapshot never carries forward findings that are absent now', () => {
  const previous = evaluateMechanicalSnapshot(
    cleanInput({ source: cleanSource({ pageTitle: '' }) }),
  );
  const current = evaluateMechanicalSnapshot({
    ...cleanInput(),
    comparisonSnapshot: previous,
  });

  assert.equal(current.findings.length, 0);
  assert.equal(current.comparisonSnapshotId, previous.snapshotId);
  assert.deepEqual(current.notReproduced, [
    {
      signature: previous.findings[0].signature,
      ruleId: 'document-title',
      target: 'site source',
      previousStatus: 'open',
      status: 'not-reproduced',
    },
  ]);
});

test('browser evidence may be incomplete without inventing a finding', () => {
  const result = evaluateMechanicalSnapshot(
    cleanInput({
      browser: [
        { target: '1440x900', completed: false, reason: 'browser automation unavailable' },
        { target: '390x844', completed: false, reason: 'browser automation unavailable' },
      ],
    }),
  );

  assert.equal(result.findings.length, 0);
  assert.deepEqual(result.passes.slice(1), [
    {
      target: '1440x900',
      kind: 'browser',
      completed: false,
      reason: 'browser automation unavailable',
    },
    {
      target: '390x844',
      kind: 'browser',
      completed: false,
      reason: 'browser automation unavailable',
    },
  ]);
});

test('source evidence may be unavailable without being reported as a clean pass', () => {
  const result = evaluateMechanicalSnapshot(
    cleanInput({
      source: { target: 'site source', completed: false, reason: 'external URL has no local source root' },
      browser: [],
    }),
  );

  assert.deepEqual(result.passes, [
    {
      target: 'site source',
      kind: 'source',
      completed: false,
      reason: 'external URL has no local source root',
    },
  ]);
  assert.equal(result.findings.length, 0);
});

test('invalid evidence is rejected instead of silently becoming success', () => {
  assert.throws(
    () => evaluateMechanicalSnapshot(cleanInput({ source: { target: 'site source' } })),
    (error) => error instanceof MechanicalInputError && error.message === 'source.completed must be a boolean',
  );
});

test('the CLI writes the same normalized contract without shell-specific behavior', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'design-studio-mechanical-'));
  const inputPath = join(directory, 'input.json');
  const outputPath = join(directory, 'output.json');
  const runtimePath = fileURLToPath(new URL('../skills/design-studio/runtime/mechanical/index.mjs', import.meta.url));
  const input = cleanInput({
    browser: [
      cleanBrowser('1440x900', 1440, 900),
      cleanBrowser('390x844', 390, 844, {
        actualViewport: { width: 391, height: 844 },
      }),
    ],
  });
  await writeFile(inputPath, JSON.stringify(input), 'utf8');

  const run = spawnSync(process.execPath, [runtimePath, inputPath, outputPath], {
    encoding: 'utf8',
  });

  assert.equal(run.status, 0, run.stderr);
  const cliResult = JSON.parse(await readFile(outputPath, 'utf8'));
  assert.deepEqual(cliResult, evaluateMechanicalSnapshot(input));
  assert.equal(cliResult.findings[0].ruleId, 'viewport-mismatch');
});
