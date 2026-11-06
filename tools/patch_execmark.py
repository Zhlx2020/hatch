import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js"

p = root / "boot.js"
s = p.read_text(encoding="utf-8")
s = s.replace('''async function refresh() {
  panels.render(await api.state());
}''',
'''async function refresh() {
  const snap = await api.state();
  panels.render(snap);
  const own = editor.file();
  if (snap.state === "stopped" && snap.line && own && snap.file === own) {
    editor.markLine(snap.line);
  } else {
    editor.markLine(0);
  }
}''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
