import assert from 'node:assert/strict';
import test from 'node:test';

import { removeBrowserProfile } from '../scripts/browser_profile_cleanup.mjs';

test('browser profile cleanup retries a transient ENOTEMPTY race', async () => {
  const calls = [];
  const waits = [];
  const remove = async (path, options) => {
    calls.push({ path, options });
    if (calls.length < 3) {
      const error = new Error('directory not empty');
      error.code = 'ENOTEMPTY';
      throw error;
    }
  };

  await removeBrowserProfile('/tmp/profile', {
    remove,
    delay: async (milliseconds) => waits.push(milliseconds),
    retryDelayMs: 25,
  });

  assert.equal(calls.length, 3);
  assert.deepEqual(waits, [25, 50]);
  for (const call of calls) {
    assert.equal(call.path, '/tmp/profile');
    assert.deepEqual(call.options, {
      recursive: true,
      force: true,
      maxRetries: 3,
      retryDelay: 25,
    });
  }
});

test('browser profile cleanup does not mask a non-retryable failure', async () => {
  const expected = Object.assign(new Error('permission denied'), { code: 'EACCES' });
  await assert.rejects(
    removeBrowserProfile('/tmp/profile', {
      remove: async () => { throw expected; },
      delay: async () => { throw new Error('delay should not run'); },
    }),
    (error) => error === expected,
  );
});
