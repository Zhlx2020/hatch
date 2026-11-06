import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/settings.py"
s = p.read_text(encoding="utf-8")

# 每个模板都显式写 -vga，界面上才看得见「有没有图形」
for old, new in [
    ('"args": ["-boot", "a", "-m", "32", "-M", "pc",\n                 "-drive", "file=%s,if=floppy,format=raw"],\n        "screen": "vnc",',
     '"args": ["-boot", "a", "-m", "32", "-M", "pc", "-vga", "std",\n                 "-drive", "file=%s,if=floppy,format=raw"],\n        "screen": "vnc",'),
    ('"args": ["-boot", "c", "-m", "64", "-M", "pc",\n                 "-drive", "file=%s,if=ide,format=raw"],\n        "screen": "vnc",',
     '"args": ["-boot", "c", "-m", "64", "-M", "pc", "-vga", "std",\n                 "-drive", "file=%s,if=ide,format=raw"],\n        "screen": "vnc",'),
    ('"args": ["-boot", "d", "-m", "64", "-M", "pc", "-cdrom", "%s"],',
     '"args": ["-boot", "d", "-m", "64", "-M", "pc", "-vga", "std", "-cdrom", "%s"],'),
    ('"args": ["-boot", "a", "-m", "128", "-M", "pc", "-smp", "2",\n                 "-drive", "file=%s,if=floppy,format=raw"],',
     '"args": ["-boot", "a", "-m", "128", "-M", "pc", "-vga", "std", "-smp", "2",\n                 "-drive", "file=%s,if=floppy,format=raw"],'),
    ('"args": ["-boot", "c", "-m", "256", "-M", "q35", "-cpu", "qemu64",\n                 "-drive", "file=%s,if=ide,format=raw"],',
     '"args": ["-boot", "c", "-m", "256", "-M", "q35", "-cpu", "qemu64", "-vga", "std",\n                 "-drive", "file=%s,if=ide,format=raw"],'),
    ('"args": ["-boot", "a", "-m", "64", "-M", "pc",\n                 "-netdev", "user,id=n0", "-device", "e1000,netdev=n0",\n                 "-drive", "file=%s,if=floppy,format=raw"],',
     '"args": ["-boot", "a", "-m", "64", "-M", "pc", "-vga", "std",\n                 "-netdev", "user,id=n0", "-device", "e1000,netdev=n0",\n                 "-drive", "file=%s,if=floppy,format=raw"],'),
    ('"args": ["-boot", "a", "-m", "32", "-M", "pc", "-no-reboot", "-no-shutdown",\n                 "-drive", "file=%s,if=floppy,format=raw"],',
     '"args": ["-boot", "a", "-m", "32", "-M", "pc", "-vga", "std", "-no-reboot", "-no-shutdown",\n                 "-drive", "file=%s,if=floppy,format=raw"],'),
    ('"name": "串口终端（无画面）",', '"name": "串口终端 · 无画面（纯文本）",'),
    ('"desc": "关掉显卡，串口当控制台：Linux 内核、bootloader 这类只看文本的活用它。"',
     '"desc": "显卡整个关掉，只剩串口文本：Linux 内核、bootloader 这类只看文本的活用它。"'),
]:
    assert old in s, old[:40]
    s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
