import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

old_start = s.index("    def _snapshot(self):")
old_end = s.index("    def eip(self):")
new = '''    def _snapshot(self):
        data = dict(self.cache)
        data.pop("state", None)
        try:
            eip = self.eip()
            data["eip"] = "%08x" % eip
            data["regs"] = self.backend.registers()
            data["disasm"] = self.backend.disassemble(eip, 8)
            data["mem"] = self.backend.hexdump(eip, 128)
            data["stack"] = self.backend.dump_stack(self._reg("esp"))
        except Exception as exc:            # a timeout must not lose the view
            data["error"] = "读取超时：%s" % exc
        data["state"] = self.arbiter.state
        data["file"] = self.file
        data["bps"] = self.breakpoints()
        data["serial"] = self.serial.since(self.cursor)[0] if self.serial else ""
        self.cache = {k: v for k, v in data.items() if k not in ("serial", "state")}
        return data

'''
s = s[:old_start] + new + s[old_end:]

s = s.replace(
    '''        try:
            return self._snapshot()
        except Exception as exc:
            self.last_error = str(exc)
            try:
                self.arbiter.to(state.FAULTED, str(exc))
            except BadTransition:
                pass
            return {"state": self.arbiter.state, "error": str(exc), "file": self.file}''',
    '''        return self._snapshot()''',
)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
