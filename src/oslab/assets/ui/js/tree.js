import * as api from "./api.js";

const treeEl = document.getElementById("tree");
const menuEl = document.getElementById("tree-menu");

let active = "";
let onOpen = () => {};
const collapsed = new Set();

const ICONS = { dir: "▸", file: "·" };

function icon(node, open) {
  if (node.kind === "dir") return open ? "▾" : "▸";
  if (node.ext === ".asm") return "▤";
  if (node.ext === ".inc") return "▦";
  return "·";
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
  const nodes = await api.tree();
  treeEl.textContent = "";
  render(treeEl, nodes || [], 0);
}

function render(parent, nodes, depth) {
  for (const node of nodes) {
    const row = document.createElement("div");
    row.className = "row " + node.kind + (node.ext ? " " + node.ext.slice(1) : "");
    row.dataset.path = node.path;
    row.style.paddingLeft = 6 + depth * 12 + "px";
    row.draggable = true;

    const mark = document.createElement("span");
    mark.className = "icon";
    mark.textContent = icon(node, !collapsed.has(node.path));
    row.append(mark);

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
    ["删除", () => drop(node)],
  ];
  for (const [label, action] of items) {
    const button = document.createElement("button");
    button.textContent = label;
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
  const base = kind === "dir" ? "newdir" : "new.asm";
  const suggested = (dir ? dir + "/" : "") + base;
  const path = window.prompt(kind === "dir" ? "目录路径" : "文件路径", suggested);
  if (!path) return;
  const out = await api.createNode(path.replace(/\/+$/, ""), kind);
  if (out.error) return say(out.error);
  await reload();
  if (kind === "file") await open(path);
}

async function promptRename(node) {
  const name = window.prompt("新名字", node.name);
  if (!name || name === node.name) return;
  const out = await api.renameNode(node.path, name);
  if (out.error) return say(out.error);
  await reload();
  setActive(out.path);
}

async function drop(node) {
  if (!window.confirm("删除 " + node.path + " ？")) return;
  const out = await api.deleteNode(node.path);
  if (out.error) return say(out.error);
  if (node.path === active) active = "";
  await reload();
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
