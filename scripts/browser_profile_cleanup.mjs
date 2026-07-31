import { rm } from 'node:fs/promises';

const RETRYABLE_REMOVAL_ERRORS = new Set([
  'EBUSY',
  'ENOTEMPTY',
  'EPERM',
]);

const wait = (milliseconds) => new Promise(
  (resolvePromise) => setTimeout(resolvePromise, milliseconds),
);

export async function removeBrowserProfile(
  profilePath,
  {
    remove = rm,
    delay = wait,
    attempts = 8,
    retryDelayMs = 100,
  } = {},
) {
  if (!Number.isInteger(attempts) || attempts < 1) {
    throw new TypeError('cleanup attempts must be a positive integer');
  }
  if (!Number.isFinite(retryDelayMs) || retryDelayMs < 0) {
    throw new TypeError('cleanup retry delay must be non-negative');
  }

  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      await remove(profilePath, {
        recursive: true,
        force: true,
        maxRetries: 3,
        retryDelay: retryDelayMs,
      });
      return;
    } catch (error) {
      lastError = error;
      if (
        !RETRYABLE_REMOVAL_ERRORS.has(error?.code)
        || attempt === attempts
      ) {
        throw error;
      }
      await delay(retryDelayMs * attempt);
    }
  }
  throw lastError;
}
