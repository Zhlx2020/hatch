import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''    def run_file(self, name):
        if not name:
            raise OsLabError("没有选中文件")
        text = workspace.read(name)
        return self.build_and_boot(text, name)

    def build_and_boot(self, text, name=""):''',
'''    def run_file(self, name, lines=None):
        if not name:
            raise OsLabError("没有选中文件")
        text = workspace.read(name)
        return self.build_and_boot(text, name, lines)

    def build_and_boot(self, text, name="", lines=None):''')

s = s.replace('''                self.bps.clear()
                self.serial = SerialBuffer(None)''',
'''                self.bps.clear()
                # 红点在构建后才有地址：先写断点，再放行，避免跑过头
                placed = []
                for line in lines or []:
                    addr = linemap.lookup(self.line_map, name, int(line))
                    if addr:
                        self.add_breakpoint(addr)
                        placed.append("%08x" % addr)
                self.serial = SerialBuffer(None)''')

s = s.replace('''                self.last_error = ""
            except Exception''',
'''                self.last_error = ""
                self.breakpoints = placed
            except Exception''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
