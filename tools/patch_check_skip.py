import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "services/checker.py"
s = p.read_text(encoding="utf-8")
s = s.replace('''def check(path, text):
    scratch''', '''def check(path, text):
    if not build.supported(path):
        return {"ok": True, "skipped": True, "errors": []}
    scratch''')
p.write_text(s, encoding="utf-8", newline="\n")

e = root / "assets/ui/js/editor.js"
t = e.read_text(encoding="utf-8")
t = t.replace('''    if (!out || out.ok !== false) {''',
              '''    if (!out || out.ok !== false || out.skipped) {''')
e.write_text(t, encoding="utf-8", newline="\n")
print("ok")
