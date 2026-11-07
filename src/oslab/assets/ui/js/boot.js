import * as api from "./api.js";
import * as dialog from "./dialog.js";
import * as detail from "./detail.js";
import * as editor from "./editor.js";
import * as settings from "./settings.js";
import * as hint from "./hint.js";
import * as marks from "./marks.js";
import * as input from "./input.js";
import * as panels from "./panels.js";
import * as screen from "./screen.js";
import * as tree from "./tree.js";

const statusEl = document.getElementById("status");
const C_RUNNABLE = [".asm", ".c"];
const CONTROLS = ["run", "pause", "cont", "step", "step-over", "reset"]
  .map((id) => document.getElementById(id));

function say(text, bad) {
  statusEl.textContent = text;
  statusEl.classList.toggle("bad", Boolean(bad));
}

async function guarded(fn) {
  for (const button of CONTROLS) button.disabled = true;
  try {
    const result = await fn();
    if (result && result.error) say(result.error, true);
    await refresh();
  } finally {
    for (const button of CONTROLS) button.disabled = false;
  }
}

let lastLive = false;
let lastHint = "";

async function refresh() {
  const snap = await api.state();
  // 只有启动中/运行中算“活”，中断之后降档
  lastLive = snap.state === "running" || snap.state === "booting";
  panels.render(snap);
  // 串口当屏幕时，只有这一拍真的带了新字符才多打一个请求
  if (panels.serialOn() && snap.serial) panels.setSerial((await api.serial()).text || "");
  const live = snap.state === "running" || snap.state === "stopped";
  // 提示条按状态变化才动，不然每拍都写一次 class 和文本，浏览器跟着重排
  const want = snap.state === "booting" ? "正在加载中…"
    : snap.state === "faulted" ? (snap.error || "启动失败")
      : live ? "" : "待机，点「运行」启动";
  const key = snap.state + "|" + want;
  if (key !== lastHint) {
    lastHint = key;
    if (want) hint.show(want, true);
    else hint.hide();
  }
  const own = editor.file();
  if (snap.state === "stopped" && snap.line && own && snap.file === own) {
    editor.markLine(snap.line);
  } else {
    editor.markLine(0);
  }
}

// 运行配置：菜单里挑一份，或者就地编辑/新建一份，跟 IDE 的 run configuration 一样
function summary(item) {
  const profile = (settings.current().profiles || []).find((one) => one.id === item.profile);
  const extra = (item.extra || []).length;
  return [item.pause_at_entry ? "停在入口" : "入口不停",
    item.action === "build" ? "只构建" : "", profile ? profile.name : item.profile,
    extra ? "附加参数 " + extra + " 项" : ""].filter(Boolean).join(" · ");
}

function paintConfigs() {
  const box = document.getElementById("run-list");
  const data = settings.current();
  box.innerHTML = "";
  for (const item of data.runs || []) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "config" + (item.name === data.active ? " on" : "");
    row.dataset.config = item.name;
    row.innerHTML = `<span class="tick">${item.name === data.active ? "✓" : ""}</span>`
      + `<span class="nm"></span><span class="meta"></span>`;
    row.querySelector(".nm").textContent = item.name;
    row.querySelector(".meta").textContent = summary(item);
    box.append(row);
  }
}

async function pickConfig(name) {
  const out = await api.saveSettings({ ...settings.current(), active: name });
  if (out && out.error) {
    say(out.error, true);
    return false;
  }
  await settings.load();
  paintConfigs();
  return true;
}

async function editConfig(mode) {
  document.getElementById("run-menu").classList.remove("open");
  const data = settings.current();
  const runs = data.runs || [];
  const creating = mode === "new";
  const source = creating
    ? { ...runs.find((one) => one.name === data.active), name: uniqueName(runs) }
    : runs.find((one) => one.name === data.active);
  if (!source) return;
  const others = new Set(runs.filter((one) => one.name !== source.name).map((one) => one.name));
  const out = await dialog.open({
    title: creating ? "新建运行配置" : "编辑运行配置",
    sub: creating ? "与当前配置同样的设置起步" : "配置：" + source.name,
    tone: "file",
    confirm: "保存",
    fields: [
      { name: "name", label: "配置名", value: source.name, mono: false,
        check: (value) => {
          const name = value.trim();
          if (!name) return "配置名不能为空";
          if (others.has(name)) return "已经有同名的配置";
          if (name.length > 20) return "最多 20 字";
          return "";
        } },
      { name: "label", label: "按钮文字", value: source.label, mono: false,
        check: (value) => (value.trim() ? "" : "按钮上得有字") },
      { name: "hint", label: "悬停提示", value: source.hint, mono: false },
      { name: "action", label: "点一下做什么", kind: "select", value: source.action,
        options: [{ value: "run", label: "构建并运行" }, { value: "build", label: "只构建" }] },
      { name: "pause_at_entry", label: "启动后立刻停在入口", kind: "check",
        value: source.pause_at_entry },
      { name: "profile", label: "QEMU 模板", kind: "select", value: source.profile,
        options: (data.profiles || []).map((one) => ({ value: one.id, label: one.name })) },
      { name: "extra", label: "附加参数", value: (source.extra || []).join(" "),
        placeholder: "-no-reboot -smp 2" },
    ],
    note: runs.length > 1 || creating ? "" : "至少要留一份配置。",
    extra: runs.length > 1
      ? [{ text: "删除这份", act: "delete" }] : [],
    onExtra: async (act) => {
      if (act !== "delete") return;
      const left = runs.filter((one) => one.name !== source.name);
      const next = left.some((one) => one.name === data.active) ? data.active : left[0].name;
      const res = await api.saveSettings({ runs: left, active: next });
      if (res.error) return say(res.error, true);
      await settings.load();
      paintConfigs();
      say("已删除配置 " + source.name);
    },
    onsubmit: async (values) => {
      const item = {
        name: values.name.trim(),
        label: values.label.trim(),
        hint: values.hint.trim(),
        action: values.action,
        pause_at_entry: Boolean(values.pause_at_entry),
        profile: values.profile,
        extra: values.extra ? values.extra.split(/\s+/).filter(Boolean) : [],
      };
      const list = creating ? [...runs, item]
        : runs.map((one) => (one.name === source.name ? item : one));
      const res = await api.saveSettings({ runs: list, active: item.name });
      if (res.error) return { error: res.error };
      await settings.load();
      paintConfigs();
      say((creating ? "已新建配置 " : "已保存配置 ") + item.name);
      return item;
    },
  });
  if (out) await boot();
}

function uniqueName(runs) {
  for (let index = 1; index < 100; index += 1) {
    const name = "配置 " + index;
    if (!runs.some((one) => one.name === name)) return name;
  }
  return "配置";
}

async function runAction(act) {
  document.getElementById("run-menu").classList.remove("open");
  if (act === "settings") return settings.open();
  if (act === "disk" || act === "elf") return detail.open(act);
  if (act === "reset") return guarded(api.reset);
  if (act === "build") return boot(true);
  if (act === "new-config") return editConfig("new");
  if (act === "edit-config") return editConfig("edit");
  return boot();
}

async function boot(forceBuild) {
  let path = editor.file() || tree.selected();
  if (path && !C_RUNNABLE.some((suffix) => path.endsWith(suffix))) {
    const first = document.querySelector("#tree .row.file");
    if (first) {
      await tree.open(first.dataset.path);
      path = tree.selected();
    }
  }
  if (!path || !C_RUNNABLE.some((suffix) => path.endsWith(suffix))) {
    say("先选一个 .asm 或 .c 文件再运行", true);
    return;
  }
  await editor.flush();
  hint.reset();
  hint.show("正在加载中…", true);
  await guarded(async () => {
    say("构建中…");
    panels.clearSerial();
    window.__ran = (window.__ran || []).concat([path, editor.breakpoints().length]);
    const onlyBuild = !!forceBuild || settings.current().run.action === "build";
    const result = await api.run(path, editor.breakpoints(), onlyBuild);
    if (result.error) say(result.error, true);
    else {
      say("已启动 " + path);
      // 地址由服务端在构建后立刻解析，这里只同步一次红点状态
      await editor.applyBreakpoints();
    }
    return result;
  });
}

document.getElementById("run").addEventListener("click", () => runAction("main"));
document.getElementById("run-more").addEventListener("click", (ev) => {
  ev.stopPropagation();
  const menu = document.getElementById("run-menu");
  if (!menu.classList.contains("open")) paintConfigs();
  menu.classList.toggle("open");
});
document.getElementById("run-menu").addEventListener("click", async (ev) => {
  const config = ev.target.closest("button[data-config]");
  if (config) {
    document.getElementById("run-menu").classList.remove("open");
    if (await pickConfig(config.dataset.config)) await boot();
    return;
  }
  const item = ev.target.closest("button[data-act]");
  if (item) runAction(item.dataset.act);
});
document.addEventListener("click", () => {
  document.getElementById("run-menu").classList.remove("open");
});
for (const button of document.querySelectorAll("[data-open]")) {
  button.addEventListener("click", () => detail.open(button.dataset.open));
}
for (const box of ["regs", "mem", "disasm"]) {
  document.getElementById(box).addEventListener("dblclick", () => detail.open(
    box === "disasm" ? "dis" : box));
}
editor.installOpen(async (path) => {
  await tree.open(path);
});
marks.install({ open: async (path, line) => {
  await tree.open(path);
  editor.markLine(line);
  window.__editorGoto?.(line);
} });
document.getElementById("step").addEventListener("click", () => guarded(api.step));
document.getElementById("step-over").addEventListener("click", () => guarded(api.stepOver));
document.getElementById("pause").addEventListener("click", () => guarded(api.pause));
document.getElementById("cont").addEventListener("click", () => guarded(api.cont));
document.getElementById("reset").addEventListener("click", () => guarded(api.reset));
document.getElementById("new-file").addEventListener("click", showTemplates);
document.getElementById("new-dir").addEventListener("click", () => tree.createIn("", "dir"));
document.getElementById("del-file").addEventListener("click", async () => {
  const path = tree.selected();
  if (!path) return say("先选一个文件", true);
  await tree.removeSelected();
  if (!tree.selected()) await editor.close();
  await tree.refresh();
});

const tplBox = document.getElementById("templates");

async function showTemplates() {
  const list = await api.templates();
  const body = document.getElementById("templates-body");
  body.textContent = "";
  if (list.error) return say(list.error, true);
  if (!list.length) {
    const empty = document.createElement("button");
    empty.textContent = "没有模板";
    body.append(empty);
  }
  for (const item of list) {
    const button = document.createElement("button");
    button.textContent = item.name;
    const summary = document.createElement("span");
    summary.className = "summary";
    summary.textContent = item.summary || "";
    button.append(summary);
    button.addEventListener("click", () => useTemplate(item.name));
    body.append(button);
  }
  tplBox.classList.add("open");
}

async function useTemplate(name) {
  const out = await dialog.open({
    title: "从模板新建",
    sub: "模板　" + name,
    confirm: "创建",
    fields: [{
      name: "dir",
      label: "放到哪个目录",
      value: name,
      check: (v) => dialog.nameProblem(v.replace(/\/+$/, ""),
        { allowSlash: true, exists: (path) => Boolean(tree.nodeAt(path)) }),
    }],
    note: "模板会写成一整个工程目录，目录要是不存在会建出来。",
    onsubmit: (data) => api.applyTemplate(name, data.dir.replace(/\/+$/, "")),
  });
  if (!out) return;
  tplBox.classList.remove("open");
  await tree.refresh();
  if (out.entry) await tree.open(out.entry);
  say("已从模板创建 " + out.dir);
}

document.getElementById("templates-close").addEventListener("click",
  () => tplBox.classList.remove("open"));

editor.install();
settings.install();
settings.load().then((conf) => panels.serialMode(conf.qemu.profile === "terminal"));
detail.install();
input.install();
screen.connect();
panels.loadSerial();
// 轮询分档：跑起来/启动中要跟手，停住了慢一拍无所谓，待机再慢些；
// 标签页在后台就干脆不跑，切回来立刻补一次。
let tick = null;
function cadence() {
  if (document.hidden) return 0;
  return lastLive ? 400 : 1500;
}
function schedule() {
  clearTimeout(tick);
  const wait = cadence();
  if (wait) tick = setTimeout(loop, wait);
}
async function loop() {
  try {
    await refresh();
  } finally {
    schedule();
  }
}
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) refresh().finally(schedule);
  schedule();
});
schedule();

tree.install((path, text) => editor.show(path, text)).then(() => {
  const first = [...document.querySelectorAll("#tree .row.file")]
    .find((row) => C_RUNNABLE.some((suffix) => row.dataset.path.endsWith(suffix)));
  if (first) tree.open(first.dataset.path);
});
