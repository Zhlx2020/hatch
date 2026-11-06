import * as api from "./api.js";
import { create } from "/ui/vendor/editor.bundle.js";

const hostEl = document.getElementById("editor-host");
const titleEl = document.getElementById("file-title");
const problemsEl = document.getElementById("problems");

let current = "";
let saveTimer = null;
let checkTimer = null;
let dead = false;
// 行号 → 地址；重启后自动重新写入，源文件改了则重解析
let pending = new Map();

const view = create(hostEl, {
  onChange: () => {
    markDirty();
    scheduleSave();
  },
  onToggleLine: (line) => {
    toggleLine(line);
  },
  onSave: (run) => {
    flush().then((result) => {
      if (run && current && (!result || result.ok !== false)) {
        document.getElementById("run").click();
      }
    });
  },
});

function markDirty() {
  titleEl.textContent = current ? current + " *" : "—";
}

function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(flush, 500);
}

function showProblems(list) {
  problemsEl.textContent = "";
  for (const item of list || []) {
    const row = document.createElement("div");
    row.className = "problem";
    if (item.line) {
      const at = document.createElement("button");
      at.className = "at";
      at.textContent = item.line + ":";
      at.addEventListener("click", () => view.markLine(item.line));
      row.append(at);
    }
    row.append(document.createTextNode(item.message));
    problemsEl.append(row);
  }
  problemsEl.classList.toggle("open", (list || []).length > 0);
}

const C_FILES = /\.(c|h)$/i;

export function show(path, text) {  if (path !== current) pending = new Map();
  current = path;
  view.setLanguage(C_FILES.test(path || "") ? "c" : "asm");
  dead = !text && !path;
  view.setValue(text || "");
  view.setDiagnostics([]);
  showProblems([]);
  titleEl.textContent = path || "—";
}

export function close() {
  show("", "");
}

export async function open(path) {
  const file = await api.readFile(path);
  if (file.error) {
    titleEl.textContent = file.error;
    return;
  }
  show(path, file.text || "");
  view.focus();
}

export function save() {
  scheduleSave();
}

export async function flush() {
  clearTimeout(saveTimer);
  if (!current || dead) return { ok: true };
  const text = view.getValue();
  const out = await api.writeFile(current, text);
  if (out.error) {
    titleEl.textContent = out.error;
    return { ok: false };
  }
  titleEl.textContent = current;
  check(text);
  return { ok: true };
}

async function check(text) {
  clearTimeout(checkTimer);
  checkTimer = setTimeout(async () => {
    if (!current) return;
    const out = await api.check(current, text);
    if (!out || out.ok !== false || out.skipped) {
      view.setDiagnostics([]);
      showProblems([]);
      return;
    }
    view.setDiagnostics(out.errors || []);
    showProblems(out.errors || []);
  }, 400);
}

async function toggleLine(line) {
  window.__bplog = (window.__bplog || []).concat(line);
  if (!current || dead) return;
  const mapped = pending.get(line);
  if (mapped) {
    pending.delete(line);
    view.setBreakpoints([...pending.keys()]);
    if (mapped.addr) await api.dropBreakpoint(mapped.addr);
    return;
  }
  const out = await api.line(current, line);
  if (!out || !out.addr) {
    pending.set(line, { addr: "" });
    view.setBreakpoints([...pending.keys()]);
    if (out && out.reason) titleEl.textContent = out.reason;
    return;
  }
  pending.set(line, { addr: out.addr });
  view.setBreakpoints([...pending.keys()]);
  await api.addBreakpoint(out.addr);
}

/** 构建成功后把红点重新解析成地址，再写入调试器。 */
export async function applyBreakpoints() {
  const lines = [...pending.keys()];
  if (!lines.length || dead) return;
  for (const line of lines) {
    const out = await api.line(current, line);
    const old = pending.get(line);
    if (old && old.addr && old.addr !== (out && out.addr)) {
      await api.dropBreakpoint(old.addr);
    }
    pending.set(line, { addr: (out && out.addr) || "" });
    if (out && out.addr) await api.addBreakpoint(out.addr);
  }
  view.setBreakpoints([...pending.keys()]);
}

export function breakpoints() {
  return [...pending.keys()];
}

export function file() {
  return current;
}

export function install() {
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") view.markLine(0);
  });
}

let lastMark = 0;

export function markLine(line) {
  if (line === lastMark) return;
  lastMark = line;
  view.markLine(line);
  if (line) view.scrollTo(line);
}
