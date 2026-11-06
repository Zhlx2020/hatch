"""Serial output: a bounded ring the UI can read by index."""
import collections
import re
import socket
import threading

from .. import config

ANSI = re.compile(r"\x1b\[[0-9;]*m")


class SerialBuffer:
    def __init__(self, backend=None, capacity=4000):
        self.backend = backend
        self._mutex = threading.Lock()
        self.connected = False
        self._sock = None
        self._stop = False
        self._lines = collections.deque(maxlen=capacity)
        self._cursor = 0
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def close(self):
        self._stop = True
        sock, self._sock = self._sock, None
        if sock:
            try:
                sock.close()
            except OSError:
                pass
        self.connected = False

    def _poll(self):
        sock = None
        while not self._stop:
            if sock is None:
                try:
                    sock = socket.create_connection((config.HOST, config.SERIAL_PORT), 0.5)
                    sock.settimeout(0.5)
                    self.connected = True
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
                self.connected = False
                if self._stop:
                    return
                continue
            if not chunk:
                sock = None
                self.connected = False
                if self._stop:
                    return
                continue
            self._trace("read %d" % len(chunk))
            text = chunk.decode("utf-8", "replace")
            with self._mutex:
                self._lines.append(text)

    def _trace(self, note):
        try:
            with open(config.RUN_DIR + "/serial.log", "a", encoding="utf-8") as fh:
                fh.write(note + "\n")
        except OSError:
            pass

    def tail(self, limit=4000):
        with self._mutex:
            return ANSI.sub("", "".join(self._lines))[-limit:]

    def since(self, cursor=0):
        with self._mutex:
            text = "".join(self._lines)
            return ANSI.sub("", text[cursor:]), len(text)
