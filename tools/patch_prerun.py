import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    '''    def build_and_boot(self, name=None):
        if name:''',
    '''    def build_and_boot(self, name=None):
        if self.arbiter.state == state.RUNNING:
            try:
                self._need_backend().pause()
            except (BackendError, BadTransition):
                pass
            self.arbiter.to(state.STOPPED, "pre-run")
        if name:''',
)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
