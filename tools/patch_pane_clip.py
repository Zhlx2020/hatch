import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/styles/panels.css"
s = p.read_text(encoding="utf-8")
s = s.replace("#disasm .bytes { color: #3f4954; width: 132px; flex: none; overflow: hidden; }",
              "#disasm .bytes { color: #3f4954; width: 104px; flex: none; overflow: hidden; }")
s = s.replace("#disasm .op { color: var(--text); }",
              "#disasm .op { color: var(--text); min-width: 0; flex: 1; overflow: hidden; text-overflow: ellipsis; }")
s = s.replace("#mem .mrow { display: flex; gap: 10px; white-space: pre; }",
              "#mem .mrow { display: flex; gap: 10px; white-space: pre; overflow: hidden; }")
s = s.replace("#mem .asis { color: #55606c; }",
              "#mem .asis { color: #55606c; flex: 1; min-width: 0; overflow: hidden; }")
s = s.replace("#mem .hex { display: flex; gap: 3px; }",
              "#mem .hex { display: flex; gap: 3px; flex: none; }")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
