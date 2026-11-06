import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

q = root / "services/session.py"
s = q.read_text(encoding="utf-8")
s = s.replace('        data["error"] = self.last_error\n',
              '        if self.last_error and "error" not in data:\n'
              '            data["error"] = self.last_error\n')
q.write_text(s, encoding="utf-8", newline="\n")

b = root / "assets/ui/js/boot.js"
t = b.read_text(encoding="utf-8")
t = t.replace('''  const first = document.querySelector("#tree .row.file");''',
              '''  const first = document.querySelector("#tree .row.file.asm")
    || document.querySelector("#tree .row.file");''')
b.write_text(t, encoding="utf-8", newline="\n")
print("ok")
