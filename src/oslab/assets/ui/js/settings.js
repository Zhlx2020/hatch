import * as api from "./api.js";
import * as panels from "./panels.js";

const box = document.getElementById("settings");
const body = document.getElementById("settings-body");
const note = document.getElementById("settings-note");
const saveBtn = document.getElementById("settings-save");
const resetBtn = document.getElementById("settings-reset");
const gear = document.getElementById("gear");
const runBtn = document.getElementById("run");

const DEFAULTS = {
  run: { label: "运行", hint: "", action: "run", pause_at_entry: true },
  qemu: { profile: "floppy", extra: [] },
};

let tab = "run";
let data = DEFAULTS;
let profiles = [];

export function esc(text) {
  return String(text == null ? "" : text)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

function paint() {
  for (const button of box.querySelectorAll("#settings-tabs button[data-tab]")) {
    button.classList.toggle("on", button.dataset.tab === tab);
  }
  body.classList.toggle("wide", false);
  if (tab === "run") {
    body.innerHTML = `<p class="acting"></p>` + `
      <label><span>按钮文字</span>
        <input id="s-label" type="text" maxlength="12" />
        <div class="hint">顶栏那个绿色按钮上的字，最多 12 个字</div>
      </label>
      <label><span>悬停提示</span>
        <input id="s-hint" type="text" maxlength="80" />
        <div class="hint">鼠标停在按钮上时显示</div>
      </label>
      <label><span>点一下做什么</span>
        <select id="s-action">
          <option value="run">构建并运行</option>
          <option value="build">只构建</option>
        </select>
        <div class="hint">按钮旁边的 ▾ 里还有复位等做法</div>
      </label>
      <label class="check"><input id="s-pause" type="checkbox" /><span>启动后立刻停在入口</span></label>
    `;
    const acting = body.querySelector(".acting");
    if (acting) acting.textContent = "正在改配置：" + data.active
      + "　（▾ 里可以新建、删除、换一份）";
    document.getElementById("s-label").value = data.run.label;
    document.getElementById("s-hint").value = data.run.hint;
    document.getElementById("s-action").value = data.run.action;
    document.getElementById("s-pause").checked = data.run.pause_at_entry;
    return;
  }
  body.innerHTML = `
    <label><span>启动模板</span>
      <select id="s-profile">
        ${profiles.map((item) => `<option value="${esc(item.id)}">${esc(item.name)}</option>`).join("")}
      </select>
    </label>
    <div class="facts">
      <div class="facts-desc" id="s-profile-desc"></div>
      <div class="facts-title">这个模板固定的参数</div>
      <table class="facts-list" id="s-profile-rows"></table>
      <div class="facts-foot">这些开关不接受手写；要别的自己在下面加，撞车会被拒。</div>
    </div>
    <label><span>附加参数（一行一个）</span>
      <textarea id="s-extra" spellcheck="false"></textarea>
      <div class="hint">模板之外的实验用：-no-reboot、-smp 2、-netdev user,id=n0 …</div>
    </label>
  `;
  const pick = document.getElementById("s-profile");
  pick.value = data.qemu.profile;
  document.getElementById("s-extra").value = (data.qemu.extra || []).join("\n");
  const describe = () => {
    const found = profiles.find((item) => item.id === pick.value);
    document.getElementById("s-profile-desc").textContent = found ? found.desc : "";
    document.getElementById("s-profile-rows").innerHTML = found
      ? (found.rows || []).map((row) => `<tr><th>${esc(row.k)}</th>`
          + `<td>${esc(row.v)}<code>${esc(row.arg)}</code></td></tr>`).join("")
      : "";
  };
  pick.addEventListener("change", describe);
  describe();
}

function collect() {
  if (tab === "run") {
    data.run.label = document.getElementById("s-label").value.trim() || "运行";
    data.run.hint = document.getElementById("s-hint").value.trim();
    data.run.action = document.getElementById("s-action").value;
    data.run.pause_at_entry = document.getElementById("s-pause").checked;
  } else {
    data.qemu.profile = document.getElementById("s-profile").value;
    data.qemu.extra = document.getElementById("s-extra").value
      .split("\n").map((line) => line.trim()).filter(Boolean);
  }
}

function say(text, bad) {
  note.textContent = text;
  note.classList.toggle("bad", !!bad);
}

export function applyRunButton() {
  runBtn.textContent = data.run.label || (data.run.action === "build" ? "构建" : "运行");
  runBtn.title = data.run.hint || "";
}

export async function load() {
  const out = await api.settings();
  profiles = out.profiles || [];
  adopt(out);
  if (box.classList.contains("open")) paint();
  return data;
}

function adopt(out) {
  data = {
    runs: out.runs || [],
    active: out.active || "",
    run: { ...DEFAULTS.run, ...(out.run || {}) },
    qemu: { ...DEFAULTS.qemu, ...(out.qemu || {}) },
  };
  applyRunButton();
}

export function current() {
  return { ...data, profiles };
}

export function open() {
  tab = "run";
  paint();
  say("改完保存，重启会话后生效");
  box.classList.add("open");
}

function close() {
  box.classList.remove("open");
}

export function install() {
  gear.addEventListener("click", () => {
    if (box.classList.contains("open")) close();
    else open();
  });
  document.getElementById("settings-close").addEventListener("click", close);
  for (const button of box.querySelectorAll("#settings-tabs button[data-tab]")) {
    button.addEventListener("click", () => {
      collect();
      tab = button.dataset.tab;
      paint();
    });
  }
  saveBtn.addEventListener("click", async () => {
    collect();
    const out = await api.saveSettings({ ...data, active: data.active });
    if (out.error) {
      say(out.error, true);
      return;
    }
    profiles = out.profiles || profiles;
    adopt(out);
    panels.serialMode(out.qemu.profile === "terminal");
    say("已保存，重启会话后生效");
  });
  resetBtn.addEventListener("click", async () => {
    const out = await api.saveSettings({ ...DEFAULTS, active: data.active });
    if (out.error) {
      say(out.error, true);
      return;
    }
    adopt(out);
    panels.serialMode(out.qemu.profile === "terminal");
    paint();
    say("这份配置已恢复默认");
  });
  load();
}
