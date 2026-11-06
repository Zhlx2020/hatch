import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''        resume = self.arbiter.state == state.RUNNING and self.backend is not None \\
            and self.backend.alive
        if resume:
            # 运行中的读不会被 gdbstub 立刻回答，得先按停（0x03）再读。
            try:
                self.backend.pause()
            except (BackendError, OSError):
                resume = False
        try:
            yield
        finally:
            if resume:
                self._resume()''',
'''        # 一次只放一组“按停→读→放开”进去，否则几路轮询会把 gdb 流搅乱。
        with self._guard:
            resume = self.arbiter.state == state.RUNNING and self.backend is not None \\
                and self.backend.alive
            if resume:
                # 运行中的读不会被 gdbstub 立刻回答，得先按停（0x03）再读。
                try:
                    self.backend.pause()
                except (BackendError, OSError):
                    resume = False
            try:
                yield
            finally:
                if resume and self.arbiter.state == state.RUNNING:
                    self._resume()''')

s = s.replace('''    def reg_detail(self):
        backend = self._need_backend()
        with self._keep_running():''',
'''    def reg_detail(self):
        with self._keep_running():
            backend = self._need_backend()''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
