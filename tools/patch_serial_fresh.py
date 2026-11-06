import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "services/serial.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    "        self._mutex = threading.Lock()\n        self.connected = False",
    "        self._mutex = threading.Lock()\n        self.connected = False\n"
    "        self._sock = None\n        self._stop = False",
)
s = s.replace(
    "    def _poll(self):\n        sock = None\n        while True:",
    "    def close(self):\n"
    "        self._stop = True\n"
    "        sock, self._sock = self._sock, None\n"
    "        if sock:\n"
    "            try:\n"
    "                sock.close()\n"
    "            except OSError:\n"
    "                pass\n"
    "        self.connected = False\n\n"
    "    def _poll(self):\n        sock = None\n        while not self._stop:",
)
s = s.replace(
    "                sock.settimeout(0.5)\n                self.connected = True",
    "                sock.settimeout(0.5)\n                self._sock = sock\n                self.connected = True",
)
s = s.replace(
    "            except OSError:\n                sock = None\n                self.connected = False\n                continue",
    "            except OSError:\n                sock = None\n                self.connected = False\n"
    "                if self._stop:\n                    return\n                continue",
)
s = s.replace(
    "            if not chunk:\n                sock = None\n                continue",
    "            if not chunk:\n                sock = None\n                self.connected = False\n"
    "                if self._stop:\n                    return\n                continue",
)
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "services/session.py"
t = q.read_text(encoding="utf-8")
t = t.replace(
    "        self.serial = SerialBuffer(None)\n        self.source = VncSource()",
    "        self.serial = None\n        self.source = VncSource()",
)
t = t.replace(
    "                self.cursor = self.serial.since(0)[1]",
    "                self.serial = SerialBuffer(None)\n"
    "                deadline = time.time() + 2.0\n"
    "                while time.time() < deadline and not self.serial.connected:\n"
    "                    time.sleep(0.02)\n"
    "                self.cursor = self.serial.since(0)[1]",
)
t = t.replace(
    "                deadline = time.time() + 2.0\n                while time.time() < deadline and not self.serial.connected:\n                    time.sleep(0.02)\n                self.cursor = self.serial.since(0)[1]\n                self.backend.cont()",
    "                self.backend.cont()",
)
t = t.replace(
    "            self.backend = None\n        wait_free()",
    "            self.backend = None\n        if self.serial:\n            self.serial.close()\n            self.serial = None\n        wait_free()",
)
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
