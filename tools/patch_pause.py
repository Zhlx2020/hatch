import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

# cache last observation, serve it while the guest runs
s = s.replace("        self.want_run = False", "        self.want_run = False\n        self.cache = {}")

s = s.replace(
    '''    def snapshot(self):
        if not self.backend or not self.backend.alive:
            return {"state": self.arbiter.state, "error": self.last_error, "file": self.file}
        try:''',
    '''    def snapshot(self):
        if not self.backend or not self.backend.alive:
            return {"state": self.arbiter.state, "error": self.last_error, "file": self.file}
        if self.arbiter.state == state.RUNNING and self.cache:
            text, cursor = self.serial.since(self.cursor) if self.serial else ("", 0)
            self.cursor = cursor
            return dict(self.cache, state=self.arbiter.state, serial=text)
        try:''',
)

s = s.replace(
    '''            "error": self.last_error,
        }

    def eip(self):''',
    '''            "error": self.last_error,
        }

    def _snapshot(self):
        data = {
            "state": self.arbiter.state,
            "file": self.file,
            "eip": "%08x" % self.eip(),
            "regs": self.backend.registers(),
            "disasm": self.backend.disassemble(self.eip(), 8),
            "stack": self.backend.dump_stack(self._reg("esp")),
            "mem": self.backend.hexdump(self.eip(), 128),
            "bps": self.breakpoints(),
            "error": self.last_error,
        }
        self.cache = {k: v for k, v in data.items() if k != "serial"}
        return data

    def eip(self):''',
)

# cont: notice a breakpoint hit
s = s.replace(
    '''    def cont(self):
        self.arbiter.guard(state.STOPPED, state.RUNNING)
        self._need_backend().cont()
        self.arbiter.to(state.RUNNING, "cont")''',
    '''    def cont(self):
        self.arbiter.guard(state.STOPPED, state.RUNNING)
        out = self._need_backend().cont()
        if "<bochs:" in out:
            self.arbiter.to(state.STOPPED, "hit")
        else:
            self.arbiter.to(state.RUNNING, "cont")
        return out

    def pause(self):
        """No async interrupt over a pipe: reset to the entry breakpoint."""
        backend = self._need_backend()
        self.arbiter.guard(state.RUNNING, state.STOPPED)
        backend.reset()
        backend.break_at(0x7C00)
        backend.cont()
        self.arbiter.to(state.STOPPED, "pause")''',
)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
