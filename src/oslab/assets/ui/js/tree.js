import * as api from "./api.js";
import * as dialog from "./dialog.js";

const treeEl = document.getElementById("tree");
const menuEl = document.getElementById("tree-menu");

let active = "";
let onOpen = () => {};
let nodes = [];
const collapsed = new Set();

const SVG = '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" '
  + 'stroke="currentColor" stroke-width="1.3" stroke-linecap="round" '
  + 'stroke-linejoin="round" aria-hidden="true">';

const CHEVRON = SVG + '<path d="M6 4l4 4-4 4"/></svg>';
const CHEVRON_DOWN = SVG + '<path d="M4 6l4 4 4-4"/></svg>';
const FOLDER = SVG + '<path d="M2 4.5A1.5 1.5 0 0 1 3.5 3h2.6c.4 0 .8.2 1 .5l.8 1h5.6A1.5 1.5 0 0 1 15 '
  + '6v6a1.5 1.5 0 0 1-1.5 1.5h-10A1.5 1.5 0 0 1 2 12z"/></svg>';
const SHEET = SVG + '<path d="M4 2.5h5l3.5 3.5V13a.5.5 0 0 1-.5.5H4a.5.5 0 0 1-.5-.5V3a.5.5 0 '
  + '0 1 .5-.5z"/><path d="M9 2.5V6h3.5"/></svg>';
const CODE = SHEET.replace("</svg>", '<path d="M6 9l-1.2 1.6L6 12.2M10 9l1.2 1.6L10 12.2"/></svg>');
const PART = SHEET.replace("</svg>", '<path d="M6 9.5h4M6 11.8h2.6"/></svg>');

function mark(row, node, open) {
  const chevron = document.createElement("span");
  chevron.className = "chev";
  const file = document.createElement("span");
  file.className = "ficon";
  if (node.kind === "dir") {
    chevron.innerHTML = open ? CHEVRON_DOWN : CHEVRON;
    file.innerHTML = FOLDER;
  } else {
    chevron.innerHTML = "";
    file.innerHTML = node.ext === ".asm" ? CODE : node.ext === ".inc" ? PART : SHEET;
  }
  row.append(chevron, file);
}

export function selected() {
  return active;
}

export function setActive(path) {
  active = path;
  for (const row of treeEl.querySelectorAll(".row")) {
    row.classList.toggle("active", row.dataset.path === path);
  }
}

async function reload() {
  nodes = (await api.tree()) || [];
  treeEl.textContent = "";
  render(treeEl, nodes, 0);
}

// 找某个目录下的同级名字，输入框拿它挡重名
function siblingsOf(dir) {
  const names = [];
  const walk = (list, parent) => {
    for (const node of list) {
      if (parent === dir) names.push(node.name);
      if (node.children) walk(node.children, node.path);
    }
  };
  walk(nodes, "");
  return names;
}

function nodeAt(path) {
  const walk = (list) => {
    for (const node of list) {
      if (node.path === path) return node;
      const hit = node.children && walk(node.children);
      if (hit) return hit;
    }
    return null;
  };
  return walk(nodes);
}

function countAll(node) {
  return (node.children || []).reduce((sum, child) => sum + 1 + countAll(child), 0);
}

function render(parent, nodes, depth) {
  for (const node of nodes) {
    const row = document.createElement("div");
    row.className = "row " + node.kind + (node.ext ? " " + node.ext.slice(1) : "");
    row.dataset.path = node.path;
    row.style.paddingLeft = 6 + depth * 12 + "px";
    row.draggable = true;

    mark(row, node, !collapsed.has(node.path));

    const label = document.createElement("span");
    label.className = "label";
    if (node.kind === "file" && node.ext) {
      label.textContent = node.name.slice(0, -node.ext.length);
      const ext = document.createElement("span");
      ext.className = "ext";
      ext.textContent = node.ext;
      label.append(ext);
    } else {
      label.textContent = node.name;
    }
    row.append(label);

    if (node.kind === "dir") {
      row.addEventListener("click", () => {
        if (collapsed.has(node.path)) collapsed.delete(node.path);
        else collapsed.add(node.path);
        reload();
      });
    } else {
      row.addEventListener("click", () => open(node.path));
    }
    row.addEventListener("contextmenu", (ev) => {
      ev.preventDefault();
      showMenu(ev, node);
    });
    row.addEventListener("dragstart", (ev) => {
      ev.dataTransfer.setData("text/plain", node.path);
      ev.dataTransfer.effectAllowed = "move";
    });
    if (node.kind === "dir") {
      row.addEventListener("dragover", (ev) => {
        ev.preventDefault();
        row.classList.add("drop");
      });
      row.addEventListener("dragleave", () => row.classList.remove("drop"));
      row.addEventListener("drop", async (ev) => {
        ev.preventDefault();
        row.classList.remove("drop");
        const from = ev.dataTransfer.getData("text/plain");
        if (from && from !== node.path) {
          const out = await api.moveNode(from, node.path);
          if (out.error) say(out.error);
          await reload();
        }
      });
    }

    parent.append(row);
    if (node.kind === "dir" && !collapsed.has(node.path)) {
      render(parent, node.children || [], depth + 1);
    }
  }
}

function say(text) {
  const status = document.getElementById("status");
  status.textContent = text;
  status.classList.add("bad");
  setTimeout(() => status.classList.remove("bad"), 2500);
}

function showMenu(ev, node) {
  menuEl.textContent = "";
  const dir = node.kind === "dir" ? node.path : node.path.split("/").slice(0, -1).join("/");
  const items = [
    ["新建文件", () => promptCreate(dir, "file")],
    ["新建目录", () => promptCreate(dir, "dir")],
    ["重命名", () => promptRename(node)],
    ["-", null],
    ["删除", () => drop(node)],
  ];
  for (const [text, action] of items) {
    if (!action) {
      const rule = document.createElement("hr");
      menuEl.append(rule);
      continue;
    }
    const button = document.createElement("button");
    button.textContent = text;
    if (text === "删除") button.classList.add("danger");
    button.addEventListener("click", () => {
      hideMenu();
      action();
    });
    menuEl.append(button);
  }
  menuEl.style.left = ev.clientX + "px";
  menuEl.style.top = ev.clientY + "px";
  menuEl.classList.add("open");
}

function hideMenu() {
  menuEl.classList.remove("open");
}

async function promptCreate(dir, kind) {
  const isDir = kind === "dir";
  const base = isDir ? "newdir" : "new.asm";
  const taken = new Set(siblingsOf(dir));
  const out = await dialog.open({
    title: isDir ? "新建目录" : "新建文件",
    sub: "位置　" + (dir || "根目录"),
    tone: isDir ? "dir" : "file",
    confirm: "创建",
    fields: [{
      name: "path",
      label: "路径",
      value: (dir ? dir + "/" : "") + base,
      placeholder: isDir ? "目录名" : "文件名",
      suffix: isDir ? "目录" : "纯文本",
      check: (value) => dialog.nameProblem(value, { allowSlash: true, taken }),
    }],
    note: isDir
      ? "带上 <span class=\"mono\">/</span> 可以一次建出多层目录。"
      : "扩展名决定按什么语言高亮；带 <span class=\"mono\">/</span> 会一起建出子目录。",
    oninput: (value, sheet, field) => {
      if (field !== "path") return;
      if (isDir) return;
      const tail = sheet.querySelector(".suffix");
      if (tail) tail.textContent = dialog.fileIcon(value.trim()) || "纯文本";
    },
    onsubmit: (data) => api.createNode(data.path.replace(/\/+$/, ""), kind),
  });
  if (!out) return;
  const path = out.path.replace(/\/+$/, "");
  await reload();
  if (!isDir) await open(path);
}

async function promptRename(node) {
  const dot = node.name.lastIndexOf(".");
  const stem = dot > 0 ? node.name.slice(0, dot) : node.name;
  const ext = dot > 0 ? node.name.slice(dot) : "";
  const parent = node.path.split("/").slice(0, -1).join("/");
  const taken = new Set(siblingsOf(parent));
  taken.delete(node.name);
  const out = await dialog.open({
    title: "重命名",
    sub: node.path,
    tone: node.kind === "dir" ? "dir" : "file",
    confirm: "改名",
    fields: node.kind === "dir"
      ? [{ name: "stem", label: "新名字", value: stem, check: (v) => dialog.nameProblem(v, { taken }) }]
      : [{ name: "stem", label: "新名字", value: stem,
          check: (v) => dialog.nameProblem(v + ext, { taken }) },
        { name: "ext", label: "后缀", value: ext, suffix: "可留空",
          check: (v) => (/^\.?[\w.+-]{0,12}$/.test(v) ? "" : "后缀只能是字母数字 . _ + -") }],
    note: "只改大小写也算改名；<b>路径会跟着变</b>，断点位置会保留。",
    onsubmit: async (data) => {
      const name = node.kind === "dir" ? data.stem : data.stem + data.ext;
      if (name === node.name) return { path: node.path };
      return api.renameNode(node.path, name);
    },
  });
  if (!out) return;
  await reload();
  setActive(out.path || node.path);
}

async function drop(node) {
  const kids = countAll(node);
  const out = await dialog.open({
    title: node.kind === "dir" ? "删除目录" : "删除文件",
    sub: node.path,
    tone: "danger",
    confirm: "删除",
    note: node.kind === "dir" && kids
      ? "整个目录连同 <b>其中 " + kids + " 项</b>一起删掉，删完不能撤销。"
      : "内容不保留，<b>删完不能撤销</b>。",
    onsubmit: () => api.deleteNode(node.path),
  });
  if (!out) return;
  if (node.path === active) active = "";
  await reload();
}

// 给工具栏的「－」用：删掉当前选中的那个
export function removeSelected() {
  return drop(nodeAt(active) || { kind: "file", path: active, name: active });
}

export function createIn(dir, kind) {
  return promptCreate(dir, kind);
}

export async function open(path) {
  const file = await api.readFile(path);
  if (file.error) return say(file.error);
  setActive(path);
  onOpen(path, file.text || "");
}

export function install(handler) {
  onOpen = handler;
  document.addEventListener("click", (ev) => {
    if (!menuEl.contains(ev.target)) hideMenu();
  });
  treeEl.addEventListener("dragover", (ev) => ev.preventDefault());
  treeEl.addEventListener("drop", async (ev) => {
    const from = ev.dataTransfer.getData("text/plain");
    if (!from) return;
    const out = await api.moveNode(from, "");
    if (out.error) return say(out.error);
    await reload();
  });
  return reload();
}

export function refresh() {
  return reload();
}
