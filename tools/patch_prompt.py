import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

start = s.index("    def _await_ready")
end = s.index("    def stop(self):")
new = '''    def _await_ready(self, timeout=10.0):
        """With no_gui_console the prompt reaches stdout, which is the ready signal."""
        end = time.time() + timeout
        while time.time() < end:
            if not self.backend.alive:
                return False
            if any("<bochs:" in line for line in self.backend.log_tail(6)):
                return True
            time.sleep(0.05)
        return False

'''
s = s[:start] + new + s[end:]

s = s.replace(
    '''                self.bps.clear()
                self.serial = SerialBuffer(self.backend)''',
    '''                self.bps.clear()
                self.serial = SerialBuffer(self.backend)
                self.backend.cont()''',
)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
