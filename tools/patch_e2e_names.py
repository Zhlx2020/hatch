import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tests/e2e/selftest.py"
s = p.read_text(encoding="utf-8")

s = s.replace('{"path": STAMP + "/t.asm", "name": "u.asm"}',
              '{"path": STAMP + "/t.asm", "name": STAMP + "-u.asm"}')
s = s.replace('out.get("path") == STAMP + "/u.asm"',
              'out.get("path") == STAMP + "/" + STAMP + "-u.asm"')
s = s.replace('{"path": STAMP + "/u.asm", "dir": ""}',
              '{"path": STAMP + "/" + STAMP + "-u.asm", "dir": ""}')
s = s.replace('"/api/file/" + STAMP + "/u.asm"',
              '"/api/file/" + STAMP + "/" + STAMP + "-u.asm"')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
