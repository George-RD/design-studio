import assert from 'node:assert/strict';
import test from 'node:test';

import { mergeMotionEvidence } from '../scripts/browser_motion_evidence.mjs';


test('motion evidence preserves each sample observation point', () => {
  const merged = mergeMotionEvidence([
    null,
    {
      observedAtMs: 150,
      prefersReducedMotion: true,
      maxMs: 400,
      activeElementCount: 2,
      samples: [
        { source: 'computed-style', id: 'first', maxMs: 400 },
        { source: 'web-animation', id: 'second', maxMs: 250 },
      ],
    },
    {
      observedAtMs: 600,
      prefersReducedMotion: true,
      maxMs: 100,
      activeElementCount: 1,
      samples: [{ source: 'computed-style', id: 'third', maxMs: 100 }],
    },
  ]);

  assert.equal(merged.prefersReducedMotion, true);
  assert.equal(merged.maxMs, 400);
  assert.equal(merged.activeElementCount, 2);
  assert.deepEqual(
    merged.samples.map(({ id, observedAtMs }) => ({ id, observedAtMs })),
    [
      { id: 'first', observedAtMs: 150 },
      { id: 'second', observedAtMs: 150 },
      { id: 'third', observedAtMs: 600 },
    ],
  );
});
