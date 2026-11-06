const regsEl = document.getElementById("regs");
const disasmEl = document.getElementById("disasm");
const memEl = document.getElementById("mem");
const bpsEl = document.getElementById("bps");
const statusEl = document.getElementById("status");

const LABELS = {
  idle: "待机",
  booting: "构建中",
  running: "运行中",
  stopped: "已中断",
  faulted: "故障",
};

const GPRS = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"];
const SEGS = ["cs", "ss", "ds", "es", "fs", "gs"];
const FLAGS = [[0, "CF"], [2, "PF"], [4, "AF"], [6, "ZF"],
               [7, "SF"], [9, "IF"], [10, "DF"], [11, "OF"]];
const REG = /^([a-z]+)\s*:\s*(?:0x)?([0-9a-f]+)$/i;
const ROW = /^([0-9a-f]{8})[:\s]{1,2}((?:[0-9a-f]{2} ?)*)\s{2,}(.*)$/i;

const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
};

function parseRegs(text) {
  const map = {};
  for (const line of String(text || "").split("\n")) {
    const m = REG.exec(line.trim());
    if (m) map[m[1].toLowerCase()] = parseInt(m[2], 16) || 0;
  }
  return map;
}

function drawRegs(text) {
  regsEl.textContent = "";
  const regs = parseRegs(text);
  if (!Object.keys(regs).length) {
    regsEl.append(el("span", "empty", "—"));
    return;
  }
  for (const name of [...GPRS, "eip"]) {
    if (regs[name] === undefined) continue;
    const value = regs[name];
    const cell = el("span", "rcell" + (name === "eip" ? " here" : ""));
    cell.append(el("span", "rn", name));
    cell.append(el("span", "rv" + (value ? "" : " zero"), "0x" + value.toString(16).padStart(8, "0")));
    regsEl.append(cell);
  }
  const flags = el("div", "rflags");
  for (const [bit, name] of FLAGS) {
    flags.append(el("span", "fl" + (((regs.eflags || 0) >>> bit) & 1 ? " on" : ""), name));
  }
  flags.append(el("span", "fl raw", "0x" + (regs.eflags || 0).toString(16).padStart(8, "0")));
  regsEl.append(flags);

  const segs = el("div", "rsegs");
  for (const name of SEGS) {
    if (regs[name] === undefined) continue;
    segs.append(el("span", "sg", name + ":" + regs[name].toString(16).padStart(4, "0")));
  }
  regsEl.append(segs);
}

function drawBps(list) {
  bpsEl.textContent = "";
  const marks = Array.isArray(list) ? list : [];
  for (const addr of marks) bpsEl.append(el("span", "bp", addr));
  bpsEl.hidden = !marks.length;
}

function splitRow(line) {
  const m = ROW.exec(line);
  if (!m) return null;
  return { addr: m[1].toLowerCase(), bytes: m[2].trim().split(/\s+/), text: m[3] };
}

function drawDisasm(text, snap) {
  disasmEl.textContent = "";
  const rows = String(text || "").split("\n").filter(Boolean);
  if (!rows.length) {
    disasmEl.append(el("span", "empty", "—"));
    return;
  }
  const marks = new Set(Array.isArray(snap.bps) ? snap.bps : []);
  for (const line of rows) {
    const row = splitRow(line);
    if (!row) continue;
    const here = row.addr === String(snap.eip || "").toLowerCase();
    const node = el("div", "drow" + (here ? " here" : ""));
    node.append(el("span", "dot" + (marks.has(row.addr) ? " on" : "")));
    node.append(el("span", "addr", row.addr));
    node.append(el("span", "bytes", row.bytes.join(" ")));
    node.append(el("span", "op", row.text));
    disasmEl.append(node);
  }
}

function drawMem(text) {
  memEl.textContent = "";
  const rows = String(text || "").split("\n").filter(Boolean);
  if (!rows.length) {
    memEl.append(el("span", "empty", "—"));
    return;
  }
  for (const line of rows) {
    const row = splitRow(line);
    if (!row) continue;
    const node = el("div", "mrow");
    node.append(el("span", "addr", row.addr));
    const hex = el("span", "hex");
    for (const byte of row.bytes) hex.append(el("span", byte === "00" ? "byte zero" : "byte", byte));
    node.append(hex);
    node.append(el("span", "asis", row.text));
    memEl.append(node);
  }
}

export function render(snap) {
  if (!snap) return;
  const label = LABELS[snap.state] || snap.state || "未知";
  statusEl.textContent = snap.error ? `${label}：${snap.error}` : label;
  statusEl.classList.toggle("bad", Boolean(snap.error) || snap.state === "faulted");
  if (snap.serial) feedSerial(snap.serial);
  if (snap.regs !== undefined) drawRegs(snap.regs);
  if (snap.disasm !== undefined) drawDisasm(snap.disasm, snap);
  if (snap.mem !== undefined) drawMem(snap.mem);
  if (snap.bps) drawBps(snap.bps);
}

// 只有在串口模板下才把串口当屏幕：其余时候文本仍留在 /api/serial 给脚本用。
const serialView = document.getElementById("serial-view");
let serialText = "";

export function serialOn() {
  return !serialView.hidden;
}

export function setSerial(text) {
  if (!serialView || serialView.textContent === text) return;
  serialView.textContent = text || "";
  serialView.scrollTop = serialView.scrollHeight;
}

export function serialMode(on) {
  document.body.classList.toggle("serial-mode", !!on);
  serialView.hidden = !on;
  if (on) serialView.scrollTop = serialView.scrollHeight;
}

export async function loadSerial() {}

export function clearSerial() {
  serialText = "";
  if (serialView) serialView.textContent = "";
}

function feedSerial(text) {
  if (!text) return;
  serialText = (serialText + text).slice(-4000);
  if (serialView) {
    serialView.textContent = serialText;
    serialView.scrollTop = serialView.scrollHeight;
  }
}
