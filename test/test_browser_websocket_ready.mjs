import assert from 'node:assert/strict';
import { test } from 'node:test';

import { waitForWebSocketOpen } from '../scripts/browser_websocket_ready.mjs';


class FakeSocket extends EventTarget {}

function controlledTimers() {
  const timer = Symbol('timer');
  let callback = null;
  const cleared = [];
  return {
    timer,
    cleared,
    setTimer(nextCallback, delay) {
      assert.equal(delay, 10_000);
      callback = nextCallback;
      return timer;
    },
    clearTimer(value) {
      cleared.push(value);
    },
    fire() {
      assert.ok(callback);
      callback();
    },
  };
}

function blockedError(message) {
  return new Error(message);
}

test('clears the connection timeout as soon as the socket opens', async () => {
  const socket = new FakeSocket();
  const timers = controlledTimers();
  const opened = waitForWebSocketOpen(socket, {
    timeoutMs: 10_000,
    setTimer: timers.setTimer,
    clearTimer: timers.clearTimer,
    errorFactory: blockedError,
  });

  socket.dispatchEvent(new Event('open'));
  await opened;

  assert.deepEqual(timers.cleared, [timers.timer]);
});

test('clears the connection timeout when the socket errors', async () => {
  const socket = new FakeSocket();
  const timers = controlledTimers();
  const opened = waitForWebSocketOpen(socket, {
    timeoutMs: 10_000,
    setTimer: timers.setTimer,
    clearTimer: timers.clearTimer,
    errorFactory: blockedError,
  });

  socket.dispatchEvent(new Event('error'));

  await assert.rejects(opened, /failed to open/);
  assert.deepEqual(timers.cleared, [timers.timer]);
});

test('rejects once when the connection timeout fires', async () => {
  const socket = new FakeSocket();
  const timers = controlledTimers();
  const opened = waitForWebSocketOpen(socket, {
    timeoutMs: 10_000,
    setTimer: timers.setTimer,
    clearTimer: timers.clearTimer,
    errorFactory: blockedError,
  });

  timers.fire();
  socket.dispatchEvent(new Event('open'));

  await assert.rejects(opened, /timed out while opening/);
  assert.deepEqual(timers.cleared, [timers.timer]);
});
