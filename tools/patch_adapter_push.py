import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

ad = root / "src/oslab/backend/qemu/adapter.py"
s = ad.read_text(encoding="utf-8")
s = s.replace('''        self._rsp.stop_reason()''', '''        self._rsp.on_stop = self.on_stop
        self._rsp.stop_reason()''')
s = s.replace('''        self._rsp = None
        self._lines = []''', '''        self._rsp = None
        self.on_stop = None            # 会话注册：状态是被推上来的
        self._lines = []''')
s = s.replace('''    def cont(self, wait=0.4):
        stop = self._need().cont(wait)
        return "stopped" if stop[:1] == b"T" else "running"

    def step(self):
        self._need().step()
        return self.registers()

    def step_over(self):
        """No disassembler in the stub: a plain step is honest here."""
        return self.step()

    def pause(self):
        self._need().interrupt()
        return "stopped"''',
'''    def cont(self):
        """发完就回；真停下来由 on_stop 回调通知。"""
        self._need().cont()

    def step(self):
        self._need().step()
        return self.registers()

    def step_over(self):
        """No disassembler in the stub: a plain step is honest here."""
        return self.step()

    def pause(self):
        self._need().interrupt()
        return "stopped"''')

# reset 之后也是靠回调知道停下
s = s.replace('''    def reset(self):
        self._need().stop_reason()
        self._need().write_reg(self._index("eip"), 0xFFF0)
        self._need().cont()''',
'''    def reset(self):
        self._need().stop_reason()
        self._need().write_reg(self._index("eip"), 0xFFF0)
        self._need().cont()''')
ad.write_text(s, encoding="utf-8", newline="\n")
print("ok")
