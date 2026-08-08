export function waitForWebSocketOpen(
  socket,
  {
    timeoutMs = 10_000,
    setTimer = setTimeout,
    clearTimer = clearTimeout,
    errorFactory = (message) => new Error(message),
  } = {},
) {
  return new Promise((resolve, reject) => {
    let settled = false;
    let timer = null;

    const cleanup = () => {
      socket.removeEventListener('open', onOpen);
      socket.removeEventListener('error', onError);
      if (timer !== null) clearTimer(timer);
    };
    const finish = (callback) => {
      if (settled) return;
      settled = true;
      cleanup();
      callback();
    };
    const onOpen = () => finish(resolve);
    const onError = () => finish(() => reject(
      errorFactory('DevTools websocket failed to open'),
    ));

    socket.addEventListener('open', onOpen);
    socket.addEventListener('error', onError);
    timer = setTimer(
      () => finish(() => reject(
        errorFactory('DevTools websocket timed out while opening'),
      )),
      timeoutMs,
    );
  });
}
