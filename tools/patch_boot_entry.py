import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

# 1) 状态里始终带上最近一次错误，界面才能显示原因
q = root / "services/session.py"
s = q.read_text(encoding="utf-8")
s = s.replace('return {"state": self.arbiter.state, "error": self.last_error, "file": self.file}',
              'return {"state": self.arbiter.state, "error": self.last_error, "file": self.file}')
s = s.replace("            return dict(self.cache, state=self.arbiter.state, file=self.file, serial=text)",
              "            return dict(self.cache, state=self.arbiter.state, file=self.file,\n"
              "                        serial=text, error=self.last_error)")
s = s.replace('        data["state"] = self.arbiter.state\n        data["file"] = self.file',
              '        data["state"] = self.arbiter.state\n        data["file"] = self.file\n'
              '        data["error"] = self.last_error')
q.write_text(s, encoding="utf-8", newline="\n")

# 2) 提示按状态显示，帧到了也只管 running/stopped
h = root / "assets/ui/js/hint.js"
h.write_text('''const el = document.getElementById("screen-hint");
const word = el.querySelector(".word");

export function show(text, force) {
  if (text) word.textContent = text;
  if (force || !el.classList.contains("live")) el.classList.add("open");
}

export function hide() {
  el.classList.remove("open");
}

export function ready() {}

export function reset() {}
''', encoding="utf-8", newline="\n")

b = root / "assets/ui/js/boot.js"
t = b.read_text(encoding="utf-8")
t = t.replace('''  if (snap.state === "booting") hint.show("正在加载中…");
  else if (snap.state === "idle") hint.show("待机，点「运行」启动");
  else if (snap.state === "faulted") hint.show(snap.error || "启动失败", true);''',
'''  const live = snap.state === "running" || snap.state === "stopped";
  if (snap.state === "booting") hint.show("正在加载中…", true);
  else if (snap.state === "faulted") hint.show(snap.error || "启动失败", true);
  else if (!live) hint.show("待机，点「运行」启动", true);
  else hint.hide();''')
t = t.replace('''async function boot() {
  const path = tree.selected();
  if (!path) {
    say("先在左边选一个要运行的 .asm", true);
    return;
  }''',
'''async function boot() {
  let path = tree.selected();
  if (path && !path.endsWith(".asm")) {
    const first = document.querySelector("#tree .row.file.asm");
    if (first) {
      await tree.open(first.dataset.path);
      path = tree.selected();
    }
  }
  if (!path || !path.endsWith(".asm")) {
    say("先选一个 .asm 再运行", true);
    return;
  }''')
b.write_text(t, encoding="utf-8", newline="\n")

# 3) 树默认选中第一个 .asm
tr = root / "assets/ui/js/tree.js"
u = tr.read_text(encoding="utf-8")
u = u.replace('  return node.ext === ".asm" ? "▤" : node.ext === ".inc" ? "▦" : "·";',
              '  return node.ext === ".asm" ? "▤" : node.ext === ".inc" ? "▦" : "·";')
tr.write_text(u, encoding="utf-8", newline="\n")
print("ok")
