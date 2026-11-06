import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

start = s.index("    def _await_ready")
end = s.index("    def stop(self):")
new = '''    def _await_ready(self, timeout=8.0):
        """Wait briefly and confirm the process holds; the debugger prompt never
        reaches stdout and a bare TCP probe would eat the single rfb client slot."""
        end = time.time() + timeout
        while time.time() < end:
            if not self.backend.alive:
                return False
            time.sleep(0.2)
            if time.time() > end - timeout + 1.2:
                return self.backend.alive
        return False

'''

s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
