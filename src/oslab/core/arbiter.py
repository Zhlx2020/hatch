"""The single arbiter: owns the lock and the only legal state machine."""
import threading

from . import state
from .errors import BadTransition


class Arbiter:
    def __init__(self):
        self._lock = threading.RLock()
        self._state = state.IDLE
        self._reason = ""

    @property
    def state(self):
        with self._lock:
            return self._state

    @property
    def reason(self):
        with self._lock:
            return self._reason

    def to(self, target, reason=""):
        with self._lock:
            if target != self._state and target not in state.ALLOWED[self._state]:
                raise BadTransition("%s -> %s" % (self._state, target))
            self._state = target
            self._reason = reason
            return self._state

    def guard(self, *expected):
        """Run a command only from one of the expected states."""
        with self._lock:
            if self._state not in expected:
                raise BadTransition("need %s, in %s" % (expected, self._state))

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, *exc):
        self._lock.release()
        return False
