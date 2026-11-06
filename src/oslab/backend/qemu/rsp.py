"""Minimal GDB remote serial protocol client (QEMU gdbstub).

一个读线程独占 socket：它只负责把到达的数据帧切出来交给 `_dispatch`。
命令线程 `_call` 发完包后在条件变量上等，不再和读线程抢 socket，
因此不会出现「两路请求互相穿插、字节流错位」的问题；`cont` 发完就返回，
停下来的 `T` 包由读线程回调出去，状态是被推上来的，不用轮询。
"""
import socket
import threading

from ...core.errors import BackendError

STOP = b"T"
RUNNING = b""
ACK = b"+"


class Rsp:
    def __init__(self, host, port, timeout=4.0):
        self.sock = socket.create_connection((host, port), timeout)
        self.sock.settimeout(None)
        self.timeout = timeout
        self.lock = threading.RLock()
        self.cond = threading.Condition(self.lock)
        self.mailbox = []
        self.waiting = 0
        self.on_stop = None            # 收到 T/W/X 时回调（会话注册）
        self.closed = False
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    # 收 ---------------------------------------------------------------
    def _read_loop(self):
        buf = b""
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while True:
                    start = buf.find(b"$")
                    if start < 0:
                        buf = b""
                        break
                    end = buf.find(b"#", start)
                    if end < 0 or len(buf) < end + 3:
                        buf = buf[start:]
                        break
                    body = buf[start + 1:end]
                    buf = buf[end + 3:]
                    self._dispatch(body)
        except OSError:
            pass
        finally:
            self.closed = True
            with self.cond:
                self.cond.notify_all()

    def _dispatch(self, body):
        with self.cond:
            waiting = self.waiting
            self.mailbox.append(body)
            self.cond.notify_all()
        # 有人在等回包的 T 是命令的答复，交给等待者；没人等的是主动停机，推给回调
        hook = self.on_stop
        if hook and not waiting and body[:1] in (STOP, b"W", b"X"):
            hook(body)

    # 发 ---------------------------------------------------------------
    def _send(self, body):
        self.sock.sendall(b"$" + body + b"#%02x" % (sum(body) & 0xFF))

    def _call(self, body, timeout=None):
        """发一条命令并等它的回包；超时抛 socket.timeout。"""
        with self.cond:
            self.mailbox.clear()
            self.waiting += 1
            try:
                self._send(body)
                deadline = timeout if timeout is not None else self.timeout
                if not self.cond.wait_for(lambda: self.mailbox or self.closed, deadline):
                    raise socket.timeout("gdbstub 无回应")
                if not self.mailbox:
                    raise BackendError("gdbstub 断开")
                return self.mailbox.pop(0)
            finally:
                self.waiting -= 1

    def wait_stop(self, timeout=3.0):
        """等下一个 T 包（已经停下就立刻从 mailbox 里取）。"""
        with self.cond:
            if self.cond.wait_for(lambda: self.mailbox or self.closed, timeout):
                return self.mailbox.pop(0) if self.mailbox else b""
            return b""

    # commands -------------------------------------------------------
    def stop_reason(self, timeout=4.0):
        return self._call(b"?", timeout)

    def read_regs(self):
        return self._call(b"g").decode("ascii", "replace")

    def write_reg(self, index, value):
        payload = value.to_bytes(4, "little").hex().encode()
        return self._call(b"P%x=%s" % (index, payload)) == b"OK"

    def read_mem(self, addr, count):
        body = self._call(b"m%x,%x" % (addr, count))
        if body.startswith(b"E"):
            raise BackendError("读内存失败 %s" % body.decode("ascii", "replace"))
        return bytes.fromhex(body.decode("ascii"))

    def breakpoint(self, addr, enable=True):
        return self._call(b"%s0,%x,1" % (b"Z" if enable else b"z", addr)) == b"OK"

    def cont(self):
        """发出去就返回；停下时由读线程回调。"""
        with self.cond:
            self._send(b"c")

    def step(self):
        return self._call(b"s")

    def interrupt(self, timeout=3.0):
        with self.cond:
            self.mailbox.clear()
            self.waiting += 1
            try:
                self.sock.sendall(b"\x03")
            finally:
                self.waiting -= 1
        return self.wait_stop(timeout)

    def detach(self):
        try:
            self._call(b"D", 1.0)
        except (OSError, BackendError, socket.timeout):
            pass

    def close(self):
        self.closed = True
        try:
            self.sock.close()
        except OSError:
            pass
