"""Minimal GDB remote serial protocol client (QEMU gdbstub)."""
import socket
import threading
import time

from ...core.errors import BackendError

STOP = b"T"
RUNNING = b""
ACK = b"+"


class Rsp:
    def __init__(self, host, port, timeout=4.0):
        self.sock = socket.create_connection((host, port), timeout)
        self.sock.settimeout(timeout)
        self.lock = threading.RLock()
        self.buffer = b""

    # framing --------------------------------------------------------
    def _send(self, body):
        self.sock.sendall(b"$" + body + b"#%02x" % (sum(body) & 0xFF))

    def _recv_packet(self, timeout=None):
        if timeout is not None:
            self.sock.settimeout(timeout)
        while True:
            char = self.sock.recv(1)
            if not char:
                raise BackendError("gdbstub 断开")
            if char == b"$":
                break
            if char in (b"+", b"-"):
                continue
        body = b""
        while True:
            char = self.sock.recv(1)
            if char == b"#":
                self.sock.recv(2)
                return body
            body += char

    # commands -------------------------------------------------------
    def stop_reason(self, timeout=4.0):
        with self.lock:
            self._send(b"?")
            return self._recv_packet(timeout)

    def read_regs(self):
        with self.lock:
            self._send(b"g")
            return self._recv_packet().decode("ascii", "replace")

    def write_reg(self, index, value):
        with self.lock:
            payload = value.to_bytes(4, "little").hex().encode()
            self._send(b"P%x=%s" % (index, payload))
            return self._recv_packet() == b"OK"

    def read_mem(self, addr, count):
        with self.lock:
            self._send(b"m%x,%x" % (addr, count))
            body = self._recv_packet()
            if body.startswith(b"E"):
                raise BackendError("读内存失败 %s" % body.decode("ascii", "replace"))
            return bytes.fromhex(body.decode("ascii"))

    def breakpoint(self, addr, enable=True):
        with self.lock:
            self._send(b"%s0,%x,1" % (b"Z" if enable else b"z", addr))
            return self._recv_packet() == b"OK"

    def cont(self, wait=0.4):
        """Continue; returns the stop packet or b'' if still running."""
        with self.lock:
            self._send(b"c")
            try:
                return self._recv_packet(wait)
            except socket.timeout:
                return RUNNING

    def step(self):
        with self.lock:
            self._send(b"s")
            return self._recv_packet()

    def interrupt(self, timeout=3.0):
        """Break into the guest. A silent stub is not fatal: return b""."""
        with self.lock:
            self.sock.sendall(b"\x03")
            try:
                return self._recv_packet(timeout)
            except socket.timeout:
                return b""

    def detach(self):
        with self.lock:
            try:
                self._send(b"D")
                self._recv_packet(1.0)
            except (OSError, BackendError):
                pass

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass
