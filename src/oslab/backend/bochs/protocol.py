"""The only place raw debugger commands live.

Commands go down stdin; the prompt carries no newline, so completion is detected
with a sentinel `print-string` instead of the prompt.
"""
import collections
import re
import threading

from ...config import SENTINEL
from ...core.errors import BackendError

BANNER = re.compile(r"<bochs:\d+>")
PROMPT = re.compile(r"<bochs:\d+>\s*$")


class Protocol:
    def __init__(self, proc):
        self.proc = proc
        self.lines = collections.deque(maxlen=4000)
        self._lock = threading.Lock()
        self._cond = threading.Condition()
        self._fed = threading.Thread(target=self._pump, daemon=True)
        self._fed.start()

    def _pump(self):
        for line in self.proc.stdout:
            with self._cond:
                self.lines.append(line.rstrip())
                self._cond.notify_all()

    def tail(self, n=20):
        with self._cond:
            return list(self.lines)[-n:]

    def run(self, command, timeout=4.0):
        """Send one command, return its output once the sentinel comes back."""
        with self._lock:
            marker = "%s_%d" % (SENTINEL, len(self.lines))
            with self._cond:
                seen = len(self.lines)
            try:
                self.proc.stdin.write("%s\nprint-string \"%s\"\n" % (command, marker))
                self.proc.stdin.flush()
            except OSError as exc:
                if self.proc.poll() is not None:
                    raise BackendError("机器已退出") from exc
                raise BackendError("写入调试器失败：%s" % exc) from exc

            collected = []
            deadline = None
            import time
            deadline = time.time() + timeout
            with self._cond:
                while True:
                    while seen < len(self.lines):
                        line = self.lines[seen]
                        seen += 1
                        if marker in line:
                            return "\n".join(collected)
                        collected.append(PROMPT.sub("", line).rstrip())
                    left = deadline - time.time()
                    if left <= 0:
                        return "\n".join(collected)
                    self._cond.wait(left)

    def shutdown(self):
        try:
            self.proc.stdin.write("q\n")
            self.proc.stdin.flush()
        except OSError:
            pass
