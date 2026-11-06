import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "workspace/keyboard.asm"
s = p.read_text(encoding="utf-8")

old = "    db 0, 0, 0, 0, 0, 0, 0, 0, 0   ; 补齐到 0x40，Shift 表从这里开始\n"
new = "    times (0x40 - ($ - table)) db 0   ; 精确补齐到 0x40，Shift 表从这里开始\n"
assert old in s
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
