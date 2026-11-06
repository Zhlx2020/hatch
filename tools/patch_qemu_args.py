import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/backend/qemu/process.py"
s = p.read_text(encoding="utf-8")
s = s.replace('"-gdb", "tcp=%s:%d"', '"-gdb", "tcp:%s:%d"')
s = s.replace('"-serial", "tcp=%s:%d,server=on,wait=off"', '"-serial", "tcp:%s:%d,server=on,wait=off"')
p.write_text(s, encoding="utf-8", newline="\n")
print([line for line in s.splitlines() if "gdb" in line or "serial" in line])
