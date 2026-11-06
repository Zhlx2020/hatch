import * as hint from "./hint.js";
import * as socket from "./socket.js";

const canvas = document.getElementById("screen");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");

let buf = new Uint8Array(0);
let width = 0;
let height = 0;
let stage = 0;
let timer = null;
let pending = 0;

const need = (n) => buf.length >= n;

function take(n) {
  const out = buf.subarray(0, n);
  buf = buf.subarray(n);
  return out;
}

function receive(chunk) {
  const merged = new Uint8Array(buf.length + chunk.length);
  merged.set(buf);
  merged.set(chunk, buf.length);
  buf = merged;
  pump();
}

function pump() {
  if (stage === 0) {
    if (!need(12)) return;
    take(12);
    socket.send(new TextEncoder().encode("RFB 003.008\n"));
    stage = 1;
  }
  if (stage === 1) {
    if (!need(1)) return;
    const count = take(1)[0];
    if (!need(count)) return;
    take(count);
    socket.send(new Uint8Array([1]));
    stage = 2;
  }
  if (stage === 2) {
    if (!need(4)) return;
    take(4);
    socket.send(new Uint8Array([1]));
    stage = 3;
  }
  if (stage === 3) {
    if (!need(24)) return;
    const head = take(24);
    width = (head[0] << 8) | head[1];
    height = (head[2] << 8) | head[3];
    pending = (head[20] << 24) | (head[21] << 16) | (head[22] << 8) | head[23];
    size();
    stage = 4;
  }
  if (stage === 4) {
    if (!need(pending)) return;
    take(pending);
    stage = 5;
    statusEl.textContent = "画面已连接";
    import("./input.js").then((m) => m.releaseAll()).catch(() => {});
    request();
    timer = setInterval(request, 60);
  }
  while (stage === 5 && need(4)) {
    const type = buf[0];
    if (type === 0) {
      if (!need(4)) return;
      const rects = (buf[2] << 8) | buf[3];
      take(4);
      for (let i = 0; i < rects; i++) {
        if (!need(12)) return;
        const rect = take(12);
        const x = (rect[0] << 8) | rect[1];
        const y = (rect[2] << 8) | rect[3];
        const w = (rect[4] << 8) | rect[5];
        const h = (rect[6] << 8) | rect[7];
        const enc = ((rect[8] << 24) | (rect[9] << 16) | (rect[10] << 8) | rect[11]) | 0;
        if (enc === -223) {
          // 客户机换分辨率：重连一次，新会话会把整屏重发，
          // 只改 canvas 大小的话 QEMU 只补变化的那块，边上会一直空着。
          width = w;
          height = h;
          size();
          clearInterval(timer);
          setTimeout(connect, 0);
          return;
        }
        if (enc !== 0) continue;
        if (!need(w * h * 4)) return;
        const px = new Uint8ClampedArray(take(w * h * 4));
        for (let i = 0; i < px.length; i += 4) {
          const b = px[i];
          px[i] = px[i + 2];
          px[i + 2] = b;
          px[i + 3] = 255;
        }
        ctx.putImageData(new ImageData(px, w, h), x, y);
        hint.ready();
      }
      continue;
    }
    if (type === 3) {
      if (!need(8)) return;
      const len = (buf[4] << 24) | (buf[5] << 16) | (buf[6] << 8) | buf[7];
      if (!need(8 + len)) return;
      take(8 + len);
      continue;
    }
    take(4);
  }
}

function size() {
  canvas.width = width;
  canvas.height = height;
  fit();
}

// 画面按客户机分辨率等比放到这块区域里：先用放得下的比例，够大时再取整，
// 免得 720x400 被拉成 720x478 那种非整数倍，字行疏密不匀、笔画糊。
function fit() {
  if (!width || !height) return;
  const wrap = canvas.parentElement;
  // clientWidth/Height 含内边距（10px + 10px），减掉才是能画的区域
  const boxW = Math.max(wrap.clientWidth - 20, 1);
  const boxH = Math.max(wrap.clientHeight - 20, 1);
  let scale = Math.min(boxW / width, boxH / height);
  if (scale >= 2) scale = Math.floor(scale);
  canvas.style.width = Math.max(1, Math.floor(width * scale)) + "px";
  canvas.style.height = Math.max(1, Math.floor(height * scale)) + "px";
}

addEventListener("resize", fit);
new ResizeObserver(fit).observe(canvas.parentElement);

export function request() {
  if (stage !== 5) return;
  const msg = new Uint8Array(10);
  msg[0] = 3;
  msg[6] = width >> 8;      // 请求区域是 x, y, 宽, 高：宽在前
  msg[7] = width & 255;
  msg[8] = height >> 8;
  msg[9] = height & 255;
  socket.send(msg);
}

export function connect() {
  stage = 0;
  buf = new Uint8Array(0);
  socket.open("/ws/screen", receive, (state) => {
    if (state === "closed") {
      statusEl.textContent = "画面已断开";
      clearInterval(timer);
    }
    if (state === "error") statusEl.textContent = "画面错误";
  });
}

export function ready() {
  return stage === 5;
}

export function frameSize() {
  return { width, height };
}
