import * as api from "./api.js";

const box = document.getElementById("marks");
const countEl = document.getElementById("mark-count");
const addEl = document.getElementById("mark-add");
const clearEl = document.getElementById("mark-clear");

let onOpen = null;
let rows = [];

export function install({ open }) {
  onOpen = open;
  addEl.addEventListener("click", () => add());
  clearEl.addEventListener("click", async () => {
    for (const row of rows) await api.dropMark(row.file, row.line);
    await load();
  });
  load();
}

async function load() {
  const out = await api.marks();
  rows = out.marks || [];
  paint();
}

function paint() {
  countEl.textContent = String(rows.length);
  box.textContent = "";
  if (!rows.length) {
    const p = document.createElement("p");
    p.className = "empty";
    p.textContent = "还没有书签。编辑器里按 F11 给当前行加一条。";
    box.append(p);
    return;
  }
  for (const row of rows) {
    const line = document.createElement("div");
    line.className = "mark" + (row.missing ? " missing" : "");
    const at = document.createElement("button");
    at.className = "at";
    at.textContent = row.file.split("/").pop() + ":" + row.line;
    at.title = row.file + (row.missing ? "（文件不在了）" : "");
    at.addEventListener("click", () => {
      if (!row.missing && onOpen) onOpen(row.file, row.line);
    });
    const text = document.createElement("span");
    text.className = "text";
    text.textContent = row.text || "";
    const drop = document.createElement("button");
    drop.className = "drop";
    drop.textContent = "×";
    drop.title = "删掉这条书签";
    drop.addEventListener("click", async (ev) => {
      ev.stopPropagation();
      await api.dropMark(row.file, row.line);
      await load();
    });
    line.append(at, text, drop);
    line.addEventListener("dblclick", () => at.click());
    box.append(line);
  }
}

/** 给当前这一行加/取消书签。 */
export async function add() {
  const where = window.__editorHere?.();
  if (!where || !where.path) return { error: "先打开一个文件" };
  const out = await api.toggleMark(where.path, where.line, where.text);
  await load();
  return out;
}

export async function refresh() {
  await load();
}

export function has(file, line) {
  return rows.some((row) => row.file === file && row.line === line);
}
