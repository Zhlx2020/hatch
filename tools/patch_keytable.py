import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "workspace/keyboard.asm"
s = p.read_text(encoding="utf-8")
old = 'db 0, "\\\\zxcvbnm,./"'
new = 'db 0, "\\zxcvbnm,./"'
assert old in s, [line for line in s.splitlines() if "zxcvbnm" in line]
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
print([line for line in s.splitlines() if "zxcvbnm" in line])
