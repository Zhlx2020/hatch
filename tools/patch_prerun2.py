import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    '''    def build_and_boot(self, text, name=""):
        with self._guard:
            self.arbiter.to(state.BOOTING, "assemble")''',
    '''    def build_and_boot(self, text, name=""):
        with self._guard:
            if self.arbiter.state == state.RUNNING:
                try:
                    self._need_backend().pause()
                    self.arbiter.to(state.STOPPED, "pre-run")
                except (BackendError, BadTransition):
                    pass
            self.arbiter.to(state.BOOTING, "assemble")''',
)
s = s.replace('raise OsLabError("Bochs 未就绪：" + " | ".join(self.backend.log_tail(6)))',
              'raise OsLabError("模拟器未就绪")')
p.write_text(s, encoding="utf-8", newline="\n")
print("pre-run" in s)
