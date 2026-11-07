import * as api from "./api.js";
import * as panels from "./panels.js";

// 按钮只负责跑；长期设置收在「启动方式」那个小浮层里
const runBtn = document.getElementById("run");
const box = document.getElementById("run-set");
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
  runBtn.textContent = data.run.label || "运行";
  runBtn.title = data.run.hint || "";
}

function paintFacts() {
  const wrap = document.getElementById("run-facts-wrap");
  const found = profiles.find((item) => item.id === data.qemu.profile);
  if (!found) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  document.getElementById("run-facts").innerHTML = `${esc(found.desc)}`
    + `<table class="facts-list">${(found.rows || []).map((row) =>
      `<tr><th>${esc(row.k)}</th><td>${esc(row.v)}<code>${esc(row.arg)}</code></td></tr>`)
      .join("")}</table>`;
}

export function paint() {
  document.getElementById("run-chips").innerHTML = profiles.map((item) =>
    `<button type="button" class="chip${item.id === data.qemu.profile ? " on" : ""}"`
    + ` data-profile="${esc(item.id)}">${esc(item.name)}</button>`).join("");
  document.getElementById("run-label").value = data.run.label;
  document.getElementById("run-hint").value = data.run.hint;
  document.getElementById("run-extra").value = (data.qemu.extra || []).join(" ");
  const disks = (data.qemu.disks || []).map((one) =>
    esc(one.path) + " → " + esc(one.iface) + (one.index ? " " + one.index : ""));
  document.getElementById("run-disks").innerHTML = (data.qemu.memory ? "内存 " + data.qemu.memory + " MB　" : "")
    + (disks.length ? "附加盘 " + disks.join("、") : "")
    + (disks.length || data.qemu.memory ? "（在 settings.toml 里改）" : "");
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

export async function load() {
  adopt(await api.settings());
  return data;
}

export function current() {
  return { ...data, profiles };
}

export function isOpen() {
  return box.classList.contains("open");
}

export function toggle() {
  if (isOpen()) {
    box.classList.remove("open");
    return;
  }
  paint();
  box.classList.add("open");
}

export function close() {
  box.classList.remove("open");
}

export function install() {
  box.addEventListener("click", (ev) => ev.stopPropagation());
  document.getElementById("run-chips").addEventListener("click", async (ev) => {
    const chip = ev.target.closest("button[data-profile]");
    if (!chip) return;
    const profile = chip.dataset.profile;
    if (await put({ qemu: { profile } })) panels.serialMode(profile === "terminal");
  });
  for (const [id, key, max] of [["run-label", "label", 12], ["run-hint", "hint", 80]]) {
    document.getElementById(id).addEventListener("change", (ev) =>
      put({ run: { [key]: ev.target.value.trim().slice(0, max) } }));
  }
  document.getElementById("run-extra").addEventListener("change", (ev) =>
    put({ qemu: { extra: ev.target.value.split(/\s+/).filter(Boolean) } }));
  load();
}
