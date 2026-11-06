import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/web/routes.py"
s = p.read_text(encoding="utf-8")
s = s.replace('    ("POST", "/api/disasm", handlers.disasm),',
              '    ("POST", "/api/disasm", handlers.disasm),\n'
              '    ("GET", "/api/line", handlers.line),')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
