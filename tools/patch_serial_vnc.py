import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "display/vnc.py"
s = p.read_text(encoding="utf-8")
old = s[s.index("    async def _skip(self, reader, head):"):s.index("    def _broadcast(self, message):")]
new = '''    async def _skip(self, reader, head):
        if head[0] == 3:
            rest = await _readn(reader, 7)
            length = struct.unpack(">I", rest[3:7])[0]
            if length:
                await _readn(reader, length)

'''
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "services/serial.py"
t = q.read_text(encoding="utf-8")
t = t.replace(
    '''import collections
import re
import threading

COM1 = 0x3F8
ANSI = re.compile(r"\\x1b\\[[0-9;]*m")''',
    '''import collections
import re
import socket
import threading

from .. import config

ANSI = re.compile(r"\\x1b\\[[0-9;]*m")''',
)
t = t.replace(
    '''    def __init__(self, backend, capacity=4000):
        self.backend = backend''',
    '''    def __init__(self, backend=None, capacity=4000):
        self.backend = backend''',
)
t = t.replace(
    '''    def _poll(self):
        import time
        while True:
            time.sleep(0.2)
            try:
                if not self.backend.alive:
                    return
                words = self.backend.read_mem(COM1 + 5, 1)
                if not words or not words[0] & 0x01:
                    continue
                ch = self.backend.read_mem(COM1, 1)[0]
            except Exception:
                return
            with self._mutex:
                self._lines.append(chr(ch))''',
    '''    def _poll(self):
        sock = None
        while True:
            if sock is None:
                try:
                    sock = socket.create_connection((config.HOST, config.SERIAL_PORT), 0.5)
                    sock.settimeout(0.5)
                except OSError:
                    import time
                    time.sleep(0.3)
                    continue
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                sock = None
                continue
            if not chunk:
                sock = None
                continue
            text = chunk.decode("utf-8", "replace")
            with self._mutex:
                self._lines.append(text)''',
)
t = t.replace(
    '''    def since(self, cursor=0):
        with self._mutex:
            text = "".join(self._lines)
            return ANSI.sub("", text[cursor:]), len(text)''',
    '''    def since(self, cursor=0):
        with self._mutex:
            text = "".join(self._lines)
            return ANSI.sub("", text[cursor:]), len(text)''',
)
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
