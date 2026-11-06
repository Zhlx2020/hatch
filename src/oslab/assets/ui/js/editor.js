import * as api from "./api.js";
import { create } from "/ui/vendor/editor.bundle.js";

const hostEl = document.getElementById("editor-host");
const titleEl = document.getElementById("file-title");
const problemsEl = document.getElementById("problems");

let current = "";
let saveTimer = null;
let checkTimer = null;
let dead = false;

const view = create(hostEl, {
  onChange: () => {
    markDirty();
    scheduleSave();
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

export function show(path, text) {
  current = path;
  dead = !text && !path;
  view.setValue(text || "");
  view.setDiagnostics([]);
  showProblems([]);
  titleEl.textContent = path || "—";
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

export function file() {
  return current;
}

export function install() {
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") view.markLine(0);
  });
}

export function markLine(line) {
  view.markLine(line);
}
