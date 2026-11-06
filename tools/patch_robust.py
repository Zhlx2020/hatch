import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

c = root / "config.py"
s = c.read_text(encoding="utf-8").replace("BOOT_TIMEOUT = 30", "BOOT_TIMEOUT = 300")
c.write_text(s, encoding="utf-8", newline="\n")

p = root / "backend/bochs/protocol.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '            except OSError as exc:\n                raise BackendError(str(exc)) from exc',
    '            except OSError as exc:\n'
    '                if self.proc.poll() is not None:\n'
    '                    raise BackendError("机器已退出") from exc\n'
    '                raise BackendError("写入调试器失败：%s" % exc) from exc',
)
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "services/session.py"
s = q.read_text(encoding="utf-8")
s = s.replace(
    '''    def snapshot(self):
        if not self.backend or not self.backend.alive:
            return {"state": self.arbiter.state, "error": self.last_error, "file": self.file}
        eip = self.eip()''',
    '''    def snapshot(self):
        if not self.backend or not self.backend.alive:
            return {"state": self.arbiter.state, "error": self.last_error, "file": self.file}
        try:
            return self._snapshot()
        except Exception as exc:
            self.last_error = str(exc)
            try:
                self.arbiter.to(state.FAULTED, str(exc))
            except BadTransition:
                pass
            return {"state": self.arbiter.state, "error": str(exc), "file": self.file}

    def _snapshot(self):
        eip = self.eip()''',
)
q.write_text(s, encoding="utf-8", newline="\n")
print("ok")
