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

}

// 串口不再占用界面：客户机写 COM1 的文本仍由 /api/serial 保留，脚本可用。
export async function loadSerial() {}

export function clearSerial() {}
