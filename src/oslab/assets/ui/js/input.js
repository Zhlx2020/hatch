import * as socket from "./socket.js";
import { ready } from "./screen.js";

const canvas = document.getElementById("screen");

// X11 keysyms for keys that have no single character.
const NAMED = {
  Enter: 0xff0d,
  Tab: 0xff09,
  Backspace: 0xff08,
  Escape: 0xff1b,
  Delete: 0xffff,
  Insert: 0xff63,
  Home: 0xff50,
  End: 0xff57,
  PageUp: 0xff55,
  PageDown: 0xff56,
  ArrowLeft: 0xff51,
  ArrowUp: 0xff52,
  ArrowRight: 0xff53,
  ArrowDown: 0xff54,
  Shift: 0xffe1,
  Control: 0xffe3,
  Alt: 0xffe9,
  Meta: 0xffe7,
  CapsLock: 0xffe5,
  " ": 0x20,
};

for (let n = 1; n <= 12; n += 1) NAMED[`F${n}`] = 0xffbe + n - 1;

function keysym(ev) {
  if (NAMED[ev.key] !== undefined) return NAMED[ev.key];
  if (NAMED[ev.code] !== undefined) return NAMED[ev.code];
  const chars = [...ev.key];
  if (chars.length !== 1) return 0;
  const code = chars[0].codePointAt(0);
  if (!code) return 0;
  if (code < 0x100) return code;
  return 0x01000000 | code;
}

function keyEvent(down, sym) {
  if (!sym) return;
  const msg = new Uint8Array(8);
  msg[0] = 4;
  msg[1] = down ? 1 : 0;
  msg[4] = (sym >>> 24) & 255;
  msg[5] = (sym >>> 16) & 255;
  msg[6] = (sym >>> 8) & 255;
  msg[7] = sym & 255;
  socket.send(msg);
}

function pointerEvent(mask, x, y) {
  const msg = new Uint8Array(6);
  msg[0] = 5;
  msg[1] = mask;
  msg[2] = (x >> 8) & 255;
  msg[3] = x & 255;
  msg[4] = (y >> 8) & 255;
  msg[5] = y & 255;
  socket.send(msg);
}

export function releaseAll() {
  for (let code = 0x20; code <= 0x7e; code += 1) keyEvent(false, code);
  for (const sym of Object.values(NAMED)) keyEvent(false, sym);
}

export function install() {
  canvas.addEventListener("keydown", (ev) => {
    if (!ready()) return;
    ev.preventDefault();
    keyEvent(true, keysym(ev));
  });
  canvas.addEventListener("keyup", (ev) => {
    if (!ready()) return;
    ev.preventDefault();
    keyEvent(false, keysym(ev));
  });
  canvas.addEventListener("mousedown", () => canvas.focus());
  canvas.addEventListener("mousemove", (ev) => {
    if (!ready() || ev.buttons === 0) return;
    const rect = canvas.getBoundingClientRect();
    pointerEvent(1, Math.round(ev.clientX - rect.left), Math.round(ev.clientY - rect.top));
  });
  canvas.addEventListener("mouseup", (ev) => {
    if (!ready()) return;
    const rect = canvas.getBoundingClientRect();
    pointerEvent(0, Math.round(ev.clientX - rect.left), Math.round(ev.clientY - rect.top));
  });
}
