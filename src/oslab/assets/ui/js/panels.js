const regsEl = document.getElementById("regs");
const disasmEl = document.getElementById("disasm");
const memEl = document.getElementById("mem");
const serialEl = document.getElementById("serial");
const bpsEl = document.getElementById("bps");
const statusEl = document.getElementById("status");

const LABELS = {
  idle: "待机",
  booting: "构建中",
  running: "运行中",
  stopped: "已中断",
  faulted: "故障",
};

export function render(snap) {
  if (!snap) return;
  const label = LABELS[snap.state] || snap.state || "未知";
  statusEl.textContent = snap.error ? `${label}：${snap.error}` : label;
  statusEl.classList.toggle("bad", Boolean(snap.error) || snap.state === "faulted");
  if (snap.regs !== undefined) regsEl.textContent = snap.regs || "—";
  if (snap.disasm !== undefined) disasmEl.textContent = snap.disasm || "—";
  if (snap.mem !== undefined) memEl.textContent = snap.mem || "—";
  if (snap.bps) {
    bpsEl.textContent = snap.bps.length ? snap.bps.join("\n") : "无";
  }
  if (snap.serial) {
    serialEl.textContent += snap.serial;
    serialEl.scrollTop = serialEl.scrollHeight;
  }
}

export async function loadSerial() {
  const res = await fetch("/api/serial");
  const data = await res.json();
  if (data.text) {
    serialEl.textContent = data.text;
    serialEl.scrollTop = serialEl.scrollHeight;
  }
}

export function clearSerial() {
  serialEl.textContent = "";
}
