import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    """                self.serial = SerialBuffer(self.backend)
                self.backend.cont()""",
    """                self.serial = SerialBuffer(self.backend)""",
)

s = s.replace(
    """                self.arbiter.to(state.RUNNING, "booted")
                self.last_error = \"\"""",
    """                self.arbiter.to(state.RUNNING, "booted")
                self.want_run = True
                threading.Thread(target=self._run_when_online, daemon=True).start()
                self.last_error = \"\"""",
)

s = s.replace(
    "    def _teardown(self):",
    '''    def _run_when_online(self, timeout=20.0):
        """Bochs blocks until an rfb client finishes the handshake; only then can
        the machine actually run, so the continue has to wait for the pump."""
        end = time.time() + timeout
        while time.time() < end:
            if not self.backend or not self.backend.alive:
                return
            if self.source.online:
                try:
                    if self.want_run:
                        self.backend.cont()
                except Exception:
                    pass
                return
            time.sleep(0.1)

    def _teardown(self):''',
)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
