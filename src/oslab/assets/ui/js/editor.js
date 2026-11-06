import * as api from "./api.js";

const codeEl = document.getElementById("code");
const titleEl = document.getElementById("file-title");

let current = "";
let saveTimer = null;

function mark(text) {
  titleEl.textContent = text;
}

export function show(path, text) {
  current = path;
  codeEl.value = text;
  mark(path);
}

export async function refresh() {
  if (!current) return;
  const file = await api.readFile(current);
  if (file.error) return;
  show(current, file.text || "");
}

export async function open(path) {
  const file = await api.readFile(path);
  if (file.error) return;
  show(path, file.text || "");
}

export async function createIn(dir) {
  const path = window.prompt("新文件路径", (dir ? dir + "/" : "") + "new.asm");
  if (!path) return "";
  const out = await api.createNode(path, "file");
  if (out.error) {
    mark(out.error);
    return "";
  }
  await open(path);
  return path;
}

export async function remove() {
  if (!current) return;
  if (!window.confirm("删除 " + current + " ？")) return;
  const out = await api.deleteNode(current);
  if (out.error) return;
  current = "";
  codeEl.value = "";
  mark("—");
}

export function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    if (current) api.writeFile(current, codeEl.value);
  }, 350);
}

export function flush() {
  clearTimeout(saveTimer);
  if (current) return api.writeFile(current, codeEl.value);
  return Promise.resolve();
}

export function file() {
  return current;
}

export function install() {
  codeEl.addEventListener("input", () => {
    mark(current ? current + " *" : "—");
    save();
  });
  codeEl.addEventListener("keydown", (ev) => {
    if (ev.key === "Tab") {
      ev.preventDefault();
      const start = codeEl.selectionStart;
      codeEl.setRangeText("    ", start, codeEl.selectionEnd, "end");
      save();
      return;
    }
    if (ev.key === "s" && (ev.ctrlKey || ev.metaKey)) {
      ev.preventDefault();
      flush();
    }
  });
}
