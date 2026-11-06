import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

# adapter: keep one map per syntax
p = root / "backend/qemu/adapter.py"
s = p.read_text(encoding="utf-8")
s = s.replace("        self._lines = []\n", "        self._lines = []\n        self._att = []\n")
s = s.replace("        self._lines = disasm.load(self._image)",
              "        self._lines = disasm.load(self._image, \"intel\")\n"
              "        self._att = disasm.load(self._image, \"att\")")
s = s.replace("        return disasm.around(self._lines, addr, count)",
              "        return disasm.around(self._pick(syntax), addr, count)")
s = s.replace("""    def disasm_rows(self, addr, count):
        return disasm.rows(self._lines, addr, count)""",
"""    def disasm_rows(self, addr, count, syntax="intel"):
        return disasm.rows(self._pick(syntax), addr, count)

    def _pick(self, syntax):
        return self._att if syntax == "att" else self._lines""")
p.write_text(s, encoding="utf-8", newline="\n")

# session: thread the syntax through
q = root / "services/session.py"
t = q.read_text(encoding="utf-8")
t = t.replace("""    def disasm_rows(self, addr, count=32):
        rows = self._need_backend().disasm_rows(addr, min(int(count), 256))""",
"""    def disasm_rows(self, addr, count=32, syntax="intel"):
        rows = self._need_backend().disasm_rows(addr, min(int(count), 256), syntax)""")
q.write_text(t, encoding="utf-8", newline="\n")

# handler: read the syntax
h = root / "web/handlers.py"
u = h.read_text(encoding="utf-8")
u = u.replace('    out = await asyncio.to_thread(session().disasm_rows, addr, count)',
              '    syntax = (body.get("syntax") or "intel").lower()\n'
              '    if syntax not in ("intel", "att"):\n'
              '        syntax = "intel"\n'
              '    out = await asyncio.to_thread(session().disasm_rows, addr, count, syntax)')
h.write_text(u, encoding="utf-8", newline="\n")

# checker: clean both listing files
c = root / "services/checker.py"
v = c.read_text(encoding="utf-8")
v = v.replace('for suffix in ("", ".asm", ".dis", ".lst"):',
              'for suffix in ("", ".asm", ".dis.intel", ".dis.att", ".lst"):')
c.write_text(v, encoding="utf-8", newline="\n")
print("ok")
