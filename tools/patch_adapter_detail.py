import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "backend/qemu/adapter.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''    def eip(self):
        return self._raw_regs()[INDEX["eip"]]''',
'''    def reg_map(self):
        """Structured registers for the detail panel."""
        words = self._raw_regs()
        out = {}
        for name in REGS:
            value = words[INDEX[name]]
            out[name] = value & (0xFFFF if name in SEGMENTS else 0xFFFFFFFF)
        return out

    def set_reg(self, name, value):
        index = self._index(name)
        word = value & (0xFFFF if name in SEGMENTS else 0xFFFFFFFF)
        self._need().write_reg(index, word)
        return word

    def eip(self):
        return self._raw_regs()[INDEX["eip"]]''')

s = s.replace('''    def hexdump(self, addr, count):''',
'''    def mem_rows(self, addr, count):
        data = self.read_mem(addr, count)
        rows = []
        for offset in range(0, len(data), 16):
            chunk = data[offset:offset + 16]
            rows.append({
                "addr": "%08x" % (addr + offset),
                "hex": ["%02x" % b for b in chunk],
                "text": "".join(chr(b) if 32 <= b < 127 else "." for b in chunk),
            })
        return rows

    def disasm_rows(self, addr, count):
        return disasm.rows(self._lines, addr, count)

    def hexdump(self, addr, count):''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
