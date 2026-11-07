import * as api from "./api.js";
import * as panels from "./panels.js";

// 启动方式的全部字段就挂在运行按钮底下那一层，改哪项当场存哪项
const runBtn = document.getElementById("run");
const menu = document.getElementById("run-menu");
const note = document.getElementById("run-note");

const DEFAULTS = {
  run: { label: "运行", hint: "", action: "run", pause_at_entry: true },
  qemu: { profile: "floppy", extra: [] },
};

let data = structuredClone(DEFAULTS);
let profiles = [];

export function esc(text) {
  return String(text == null ? "" : text)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

export function applyRunButton() {
  runBtn.textContent = data.run.label || (data.run.action === "build" ? "构建" : "运行");
  runBtn.title = data.run.hint || "";
}

function paintFacts() {
  const box = document.getElementById("run-facts");
  const found = profiles.find((item) => item.id === data.qemu.profile);
  if (!found) {
    box.innerHTML = "";
    return;
  }
  box.innerHTML = `<div class="dim">${esc(found.desc)}</div>`
    + `<table class="facts-list">${(found.rows || []).map((row) =>
      `<tr><th>${esc(row.k)}</th><td>${esc(row.v)}<code>${esc(row.arg)}</code></td></tr>`)
      .join("")}</table>`
    + `<div class="dim">模板固定的参数不接受手写；要别的写在附加参数里，撞车会被拒。</div>`;
}

// 浮层每次打开都按当前值重画一遍
export function paint() {
  for (const button of document.querySelectorAll("#run-action button")) {
    button.classList.toggle("on", button.dataset.do === data.run.action);
  }
  document.getElementById("run-pause").checked = data.run.pause_at_entry;
  document.getElementById("run-label").value = data.run.label;
  document.getElementById("run-hint").value = data.run.hint;
  const pick = document.getElementById("run-profile");
  pick.innerHTML = profiles.map((item) =>
    `<option value="${esc(item.id)}">${esc(item.name)}</option>`).join("");
  pick.value = data.qemu.profile;
  document.getElementById("run-extra").value = (data.qemu.extra || []).join(" ");
  paintFacts();
}

function say(text, bad) {
  note.textContent = text;
  note.classList.toggle("bad", !!bad);
}

function adopt(out) {
  data = {
    run: { ...DEFAULTS.run, ...(out.run || {}) },
    qemu: { ...DEFAULTS.qemu, ...(out.qemu || {}) },
  };
  profiles = out.profiles || profiles;
  applyRunButton();
}

async function put(patch) {
  const out = await api.saveSettings(patch);
  if (out.error) {
    say(out.error, true);
    await load();
    paint();
    return false;
  }
  adopt(out);
  paint();
  // 模板和附加参数只影响下次开机；按钮长相当场就换
  say(patch.qemu ? "已保存，下次启动生效" : "已保存");
  return true;
}

export function setAction(action) {
  return put({ run: { action } });
}

export async function load() {
  adopt(await api.settings());
  return data;
}

export function current() {
  return { ...data, profiles };
}

export function install() {
  menu.addEventListener("click", (ev) => ev.stopPropagation());
  document.getElementById("run-action").addEventListener("click", (ev) => {
    const button = ev.target.closest("button[data-do]");
    if (button) setAction(button.dataset.do);
  });
  document.getElementById("run-pause").addEventListener("change", (ev) =>
    put({ run: { pause_at_entry: ev.target.checked } }));
  for (const [id, key, max] of [["run-label", "label", 12], ["run-hint", "hint", 80]]) {
    document.getElementById(id).addEventListener("change", (ev) =>
      put({ run: { [key]: ev.target.value.trim().slice(0, max) } }));
  }
  document.getElementById("run-profile").addEventListener("change", async (ev) => {
    const profile = ev.target.value;
    if (await put({ qemu: { profile } })) panels.serialMode(profile === "terminal");
  });
  document.getElementById("run-extra").addEventListener("change", (ev) =>
    put({ qemu: { extra: ev.target.value.split(/\s+/).filter(Boolean) } }));
  load();
}
