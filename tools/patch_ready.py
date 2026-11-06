import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

old = '''    def _await_ready(self, timeout=10.0):
        end = time.time() + timeout
        while time.time() < end:
            if not self.backend.alive:
                return False
            if any("<bochs:" in line for line in self.backend.log_tail(4)):
                return True
            time.sleep(0.05)
        return False'''

new = '''    def _await_ready(self, timeout=15.0):
        """Ready means the rfb port accepts; the debugger prompt never reaches stdout."""
        end = time.time() + timeout
        while time.time() < end:
            if not self.backend.alive:
                return False
            try:
                socket.create_connection((config.HOST, config.RFB_PORT), 0.3).close()
                return True
            except OSError:
                time.sleep(0.05)
        return False'''

assert old in s, "pattern missing"
s = s.replace(old, new)
s = s.replace("import os\nimport re", "import os\nimport re\nimport socket")
s = s.replace("from ..backend.bochs.adapter import BochsBackend",
              "from .. import config\nfrom ..backend.bochs.adapter import BochsBackend")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
