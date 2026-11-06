import pathlib
import re

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

# assembler: also emit a source listing
p = root / "services/assembler.py"
s = p.read_text(encoding="utf-8")
s = s.replace('args = [config.NASM, "-f", "bin", asm, "-o", out_path]',
              'args = [config.NASM, "-f", "bin", asm, "-o", out_path, "-l", out_path + ".lst"]')
p.write_text(s, encoding="utf-8", newline="\n")

# new module: address -> source line
(root / "services/sourcemap.py").write_text(
    '''"""Map machine addresses back to source lines using the nasm listing."""
import os
import re

LINE = re.compile(r"^\\s*(\\d+)\\s+([0-9A-Fa-f]{8})\\s")


def load(image):
    path = image + ".lst"
    table = {}
    if not os.path.exists(path):
        return table
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            match = LINE.match(raw)
            if match:
                table[int(match.group(2), 16)] = int(match.group(1))
    return table


def line_at(table, addr):
    if not table:
        return 0
    for probe in range(0, 16):
        found = table.get(addr - probe)
        if found:
            return found
    return 0
''',
    encoding="utf-8",
    newline="\n",
)

# session: keep the map and expose the current line while stopped
q = root / "services/session.py"
t = q.read_text(encoding="utf-8")
t = t.replace("from . import build, workspace", "from . import build, sourcemap, workspace")
t = t.replace("                build.build(text, name, self.image)",
              "                build.build(text, name, self.image)\n"
              "                self.source_map = sourcemap.load(self.image)")
t = t.replace('        data["stack"] = self.backend.dump_stack(self._reg("esp"))',
              '        data["stack"] = self.backend.dump_stack(self._reg("esp"))\n'
              '            data["line"] = sourcemap.line_at(self.source_map, eip)')
q.write_text(t, encoding="utf-8", newline="\n")

# init slot
t = q.read_text(encoding="utf-8")
t = t.replace("        self.bps = set()", "        self.bps = set()\n        self.source_map = {}")
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
