import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js"

(root / "hint.js").write_text(
    '''const el = document.getElementById("screen-hint");
const word = el.querySelector(".word");

let frames = 0;

export function show(text, force) {
  if (text) word.textContent = text;
  if (force || frames === 0) el.classList.add("open");
}

export function hide() {
  el.classList.remove("open");
}

export function ready() {
  frames += 1;
  if (frames === 1) hide();
}

export function reset() {
  frames = 0;
}
''',
    encoding="utf-8",
    newline="\n",
)

b = root / "boot.js"
s = b.read_text(encoding="utf-8")
s = s.replace('import * as editor from "./editor.js";',
              'import * as editor from "./editor.js";\nimport * as hint from "./hint.js";')
s = s.replace('''  const snap = await api.state();
  panels.render(snap);''',
'''  const snap = await api.state();
  panels.render(snap);
  if (snap.state === "booting") hint.show("正在加载中…");
  else if (snap.state === "idle") hint.show("待机，点「运行」启动");
  else if (snap.state === "faulted") hint.show(snap.error || "启动失败", true);''')
s = s.replace('''  await editor.flush();
  await guarded(async () => {
    say("构建中…");
    panels.clearSerial();''',
'''  await editor.flush();
  hint.reset();
  hint.show("正在加载中…", true);
  await guarded(async () => {
    say("构建中…");
    panels.clearSerial();''')
b.write_text(s, encoding="utf-8", newline="\n")

sc = root / "screen.js"
t = sc.read_text(encoding="utf-8")
t = t.replace('import * as socket from "./socket.js";',
              'import * as hint from "./hint.js";\nimport * as socket from "./socket.js";')
t = t.replace("        ctx.putImageData(new ImageData(px, w, h), x, y);",
              "        ctx.putImageData(new ImageData(px, w, h), x, y);\n        hint.ready();")
sc.write_text(t, encoding="utf-8", newline="\n")
print("ok")
