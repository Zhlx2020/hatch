import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "services/session.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'REG_LINE = re.compile(r"^(eip|rip):\\s*([0-9a-fA-F]+)")',
    'REG_LINE = re.compile(r"^(eip|rip):\\s*(?:0x)?([0-9a-fA-F]+)")',
)
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "backend/qemu/adapter.py"
t = q.read_text(encoding="utf-8")
t = t.replace(
    "    def dump_stack(self, esp):\n        return self.hexdump(esp & 0xFFFFFFFF, 64)",
    "    def dump_stack(self, esp):\n"
    "        value = int(esp, 16) if isinstance(esp, str) else int(esp)\n"
    "        return self.hexdump(value & 0xFFFFFFFF, 64)",
)
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
