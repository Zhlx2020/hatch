let socket = null;
let handler = null;
let retry = null;

export function open(path, onMessage, onState) {
  handler = onMessage;
  const connect = () => {
    socket = new WebSocket(`ws://${location.host}${path}`);
    socket.binaryType = "arraybuffer";
    socket.onopen = () => onState("open");
    socket.onclose = () => {
      onState("closed");
      retry = setTimeout(connect, 800);
    };
    socket.onerror = () => onState("error");
    socket.onmessage = (ev) => handler && handler(new Uint8Array(ev.data));
  };
  connect();
}

export function send(bytes) {
  if (socket && socket.readyState === WebSocket.OPEN) socket.send(bytes);
}

export function close() {
  clearTimeout(retry);
  if (socket) socket.close();
  socket = null;
  handler = null;
}
