import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''                self.line_map = line_map or linemap.from_listing(self.image, name)''',
'''                self.line_map = line_map or linemap.from_listing(self.image, name)
                current_lines = self.line_map.get(workspace.safe(name)) or {}
                if current_lines:      # C 的地址反查也走同一张表
                    self.source_map = {addr: line for line, addr in current_lines.items()}''')

s = s.replace('''                self.cursor = 0
                self.backend.cont()
                self.file = name
                self.arbiter.to(state.RUNNING, "booted")''',
'''                self.cursor = 0
                self.file = name
                hit = self.backend.cont()
                if hit == "stopped":
                    self.arbiter.to(state.STOPPED, "hit")
                else:
                    self.arbiter.to(state.RUNNING, "booted")''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
