import * as api from "./api.js";
import * as dialog from "./dialog.js";
import * as detail from "./detail.js";
import * as editor from "./editor.js";
import * as settings from "./settings.js";
import * as hint from "./hint.js";
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

async function refresh() {
  const snap = await api.state();
  panels.render(snap);
  if (panels.serialOn()) panels.setSerial((await api.serial()).text || "");
  const live = snap.state === "running" || snap.state === "stopped";
  if (snap.state === "booting") hint.show("正在加载中…", true);
  else if (snap.state === "faulted") hint.show(snap.error || "启动失败", true);
  else if (!live) hint.show("待机，点「运行」启动", true);
  else hint.hide();
  const own = editor.file();
  if (snap.state === "stopped" && snap.line && own && snap.file === own) {
    editor.markLine(snap.line);
  } else {
    editor.markLine(0);
  }
}

async function runAction(act) {
  document.getElementById("run-menu").classList.remove("open");
  if (act === "settings") return settings.open();
  if (act === "reset") return guarded(api.reset);
  if (act === "build") return boot(true);
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
  document.getElementById("run-menu").classList.toggle("open");
});
document.getElementById("run-menu").addEventListener("click", (ev) => {
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
      check: (v) => dialog.nameProblem(v.replace(/\/+$/, ""), { allowSlash: true }),
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
setInterval(refresh, 400);

tree.install((path, text) => editor.show(path, text)).then(() => {
  const first = [...document.querySelectorAll("#tree .row.file")]
    .find((row) => C_RUNNABLE.some((suffix) => row.dataset.path.endsWith(suffix)));
  if (first) tree.open(first.dataset.path);
});
