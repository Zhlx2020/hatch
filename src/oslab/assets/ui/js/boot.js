import * as api from "./api.js";
import * as detail from "./detail.js";
import * as editor from "./editor.js";
import * as input from "./input.js";
import * as panels from "./panels.js";
import * as screen from "./screen.js";
import * as tree from "./tree.js";

const statusEl = document.getElementById("status");
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
  const own = editor.file();
  if (snap.state === "stopped" && snap.line && own && snap.file === own) {
    editor.markLine(snap.line);
  } else {
    editor.markLine(0);
  }
}

async function boot() {
  const path = tree.selected();
  if (!path) {
    say("先在左边选一个要运行的 .asm", true);
    return;
  }
  await editor.flush();
  await guarded(async () => {
    say("构建中…");
    panels.clearSerial();
    const result = await api.run(path);
    if (result.error) say(result.error, true);
    else say("已启动 " + path);
    return result;
  });
}

document.getElementById("run").addEventListener("click", boot);
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
document.getElementById("new-file").addEventListener("click", () => editor.createIn(""));
document.getElementById("new-dir").addEventListener("click", async () => {
  const path = window.prompt("新目录路径", "src");
  if (!path) return;
  const out = await api.createNode(path, "dir");
  if (out.error) say(out.error, true);
  await tree.refresh();
});
document.getElementById("del-file").addEventListener("click", async () => {
  await editor.remove();
  await tree.refresh();
});

editor.install();
detail.install();
input.install();
screen.connect();
panels.loadSerial();
setInterval(refresh, 400);

tree.install((path, text) => editor.show(path, text)).then(() => {
  const first = document.querySelector("#tree .row.file");
  if (first) tree.open(first.dataset.path);
});
