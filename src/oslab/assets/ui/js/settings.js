import * as api from "./api.js";

const box = document.getElementById("settings");
const body = document.getElementById("settings-body");
const note = document.getElementById("settings-note");
const saveBtn = document.getElementById("settings-save");
const resetBtn = document.getElementById("settings-reset");
const gear = document.getElementById("gear");
const runBtn = document.getElementById("run");

const DEFAULTS = {
  run: { label: "运行", hint: "", action: "run", pause_at_entry: true },
  qemu: { memory: 32, machine: "pc", cpu: "", extra: [] },
};

const FIELDS = {
  run: () => `
    <label><span>按钮文字</span>
      <input id="s-label" type="text" maxlength="12" value="${esc(DEFAULTS.run.label)}" />
      <div class="hint">顶栏那个绿色按钮上的字，最多 12 个字</div>
    </label>
    <label><span>悬停提示</span>
      <input id="s-hint" type="text" maxlength="80" value="" />
      <div class="hint">鼠标停在按钮上时显示</div>
    </label>
    <label><span>点击后</span>
      <select id="s-action">
        <option value="run">构建并运行</option>
        <option value="build">只构建</option>
      </select>
    </label>
    <label class="check"><input id="s-pause" type="checkbox" checked /><span>启动后立刻停在入口</span></label>
  `,
  qemu: () => `
    <label><span>内存（MB，4–512）</span>
      <input id="s-mem" type="number" min="4" max="512" value="32" />
      <div class="hint">这台机器只跑引导扇区，一般 16–64 就够</div>
    </label>
    <label><span>机器类型</span>
      <input id="s-machine" type="text" maxlength="40" value="pc" />
      <div class="hint">默认 pc；改成 isapc 能去掉多余设备</div>
    </label>
    <label><span>CPU 型号（可留空）</span>
      <input id="s-cpu" type="text" maxlength="40" value="" />
      <div class="hint">例如 486、pentium；留空由 QEMU 选</div>
    </label>
    <label><span>附加参数（一行一个）</span>
      <textarea id="s-extra" spellcheck="false"></textarea>
      <div class="hint">白名单：-no-reboot -no-shutdown -smp N -rtc base=utc -vga std …</div>
    </label>
  `,
};

let tab = "run";
let data = DEFAULTS;

export function esc(text) {
  return String(text == null ? "" : text)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

function paint() {
  for (const button of box.querySelectorAll("#settings-tabs button[data-tab]")) {
    button.classList.toggle("on", button.dataset.tab === tab);
  }
  body.innerHTML = FIELDS[tab]();
  if (tab === "run") {
    document.getElementById("s-label").value = data.run.label;
    document.getElementById("s-hint").value = data.run.hint;
    document.getElementById("s-action").value = data.run.action;
    document.getElementById("s-pause").checked = data.run.pause_at_entry;
  } else {
    document.getElementById("s-mem").value = data.qemu.memory;
    document.getElementById("s-machine").value = data.qemu.machine;
    document.getElementById("s-cpu").value = data.qemu.cpu;
    document.getElementById("s-extra").value = (data.qemu.extra || []).join("\n");
  }
}

function collect() {
  if (tab === "run") {
    data.run.label = document.getElementById("s-label").value.trim() || "运行";
    data.run.hint = document.getElementById("s-hint").value.trim();
    data.run.action = document.getElementById("s-action").value;
    data.run.pause_at_entry = document.getElementById("s-pause").checked;
  } else {
    data.qemu.memory = Number(document.getElementById("s-mem").value) || 32;
    data.qemu.machine = document.getElementById("s-machine").value.trim();
    data.qemu.cpu = document.getElementById("s-cpu").value.trim();
    data.qemu.extra = document.getElementById("s-extra").value
      .split("\n").map((line) => line.trim()).filter(Boolean);
  }
}

function say(text, bad) {
  note.textContent = text;
  note.classList.toggle("bad", !!bad);
}

export function applyRunButton() {
  const label = data.run.action === "build" ? (data.run.label || "构建") : data.run.label;
  runBtn.textContent = label || "运行";
  runBtn.title = data.run.hint || "";
}

export async function load() {
  const out = await api.settings();
  data = {
    run: { ...DEFAULTS.run, ...(out.run || {}) },
    qemu: { ...DEFAULTS.qemu, ...(out.qemu || {}) },
  };
  applyRunButton();
  if (box.classList.contains("open")) paint();
  return data;
}

export function current() {
  return data;
}

export function open() {
  tab = "run";
  paint();
  say("改完重启会话后生效");
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
    const out = await api.saveSettings(data);
    if (out.error) {
      say(out.error, true);
      return;
    }
    data = out;
    applyRunButton();
    say("已保存，重启会话后生效");
  });
  resetBtn.addEventListener("click", async () => {
    const out = await api.saveSettings(DEFAULTS);
    if (out.error) {
      say(out.error, true);
      return;
    }
    data = out;
    applyRunButton();
    paint();
    say("已恢复默认");
  });
  load();
}
