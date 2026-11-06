import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    "from ..backend.bochs.adapter import BochsBackend\nfrom ..backend.bochs.process import make_session_dir",
    "from ..backend.bochs.adapter import BochsBackend\n"
    "from ..backend.bochs.process import make_session_dir\n"
    "from ..backend.qemu.adapter import QemuBackend\n"
    "from ..backend.qemu.process import make_session_dir as make_qemu_dir",
)
s = s.replace("from ..display.rfb import RfbSource", "from ..display.rfb import RfbSource\nfrom ..display.vnc import VncSource")

s = s.replace(
    '''        self.dir = make_session_dir()''',
    '''        self.dir = make_qemu_dir()''',
)
s = s.replace(
    '''        self.source = RfbSource()''',
    '''        self.source = VncSource()''',
)
s = s.replace(
    "                self.backend = BochsBackend(self.dir, self.image)",
    "                self.backend = QemuBackend(self.dir, self.image)",
)

# ready: gdb stub is up as soon as start() returns
start = s.index("    def _await_ready")
end = s.index("    def stop(self):")
s = s[:start] + '''    def _await_ready(self, timeout=8.0):
        return self.backend.alive

''' + s[end:]

# QEMU keeps running while the debugger is attached: no online dance needed
s = s.replace(
    '''                self.want_run = True
                threading.Thread(target=self._run_when_online, daemon=True).start()''',
    "",
)
s = s.replace(
    '''                self.serial = SerialBuffer(self.backend)''',
    '''                self.serial = SerialBuffer(None)
                self.backend.cont()''',
)

# pause now really interrupts
s = s.replace(
    '''    def pause(self):
        """No async interrupt over a pipe: reset to the entry breakpoint."""
        backend = self._need_backend()
        self.arbiter.guard(state.RUNNING, state.STOPPED)
        backend.reset()
        backend.break_at(0x7C00)
        backend.cont()
        self.arbiter.to(state.STOPPED, "pause")''',
    '''    def pause(self):
        self.arbiter.guard(state.RUNNING)
        self._need_backend().pause()
        self.arbiter.to(state.STOPPED, "pause")
        return "paused"''',
)

s = s.replace(
    '''        out = self._need_backend().cont()
        if "<bochs:" in out:
            self.arbiter.to(state.STOPPED, "hit")
        else:
            self.arbiter.to(state.RUNNING, "cont")
        return out''',
    '''        result = self._need_backend().cont()
        if result == "stopped":
            self.arbiter.to(state.STOPPED, "hit")
        else:
            self.arbiter.to(state.RUNNING, "cont")
        return result''',
)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
