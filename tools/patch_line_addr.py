import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace("        self.source_map = {}", "        self.source_map = {}\n        self.line_map = {}")

s = s.replace('''    def disasm_rows(self''',
'''    def line_addr(self, path, line):
        """Address of a source line from the last build, or 0."""
        return linemap.lookup(self.line_map, path, int(line))

    def disasm_rows(self''')
p.write_text(s, encoding="utf-8", newline="\n")

h = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/web/handlers.py"
t = h.read_text(encoding="utf-8")
print("line_addr" in t)
