import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "services/serial.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "        self._mutex = threading.Lock()",
    "        self._mutex = threading.Lock()\n        self.connected = False",
)
s = s.replace(
    "                sock.settimeout(0.5)",
    "                sock.settimeout(0.5)\n                    self.connected = True",
)
s = s.replace(
    "            except OSError:\n                sock = None\n                continue",
    "            except OSError:\n                sock = None\n                self.connected = False\n                continue",
)
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "services/session.py"
t = q.read_text(encoding="utf-8")
t = t.replace(
    "                self.cursor = self.serial.since(0)[1]\n                self.backend.cont()",
    "                deadline = time.time() + 2.0\n"
    "                while time.time() < deadline and not self.serial.connected:\n"
    "                    time.sleep(0.02)\n"
    "                self.cursor = self.serial.since(0)[1]\n"
    "                self.backend.cont()",
)
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
