"""QEMU process: vnc screen, gdb stub and serial on fixed local ports."""
import os
import subprocess
import time

from ... import config

ARGS = [
    "-m", "32",
    "-boot", "a",
    "-display", "vnc=127.0.0.1:%d" % config.VNC_HOST_PORT,
    "-gdb", "tcp:%s:%d" % (config.HOST, config.GDB_PORT),
    "-serial", "tcp:%s:%d,server=on,wait=off" % (config.HOST, config.SERIAL_PORT),
    "-monitor", "none",
    "-S",
    "-drive", "file=%s,if=floppy,format=raw",
]


def make_session_dir():
    os.makedirs(config.RUN_DIR, exist_ok=True)
    n = 1
    while os.path.exists(os.path.join(config.RUN_DIR, "q%02d" % n)):
        n += 1
    path = os.path.join(config.RUN_DIR, "q%02d" % n)
    os.makedirs(path)
    return path


class QemuProcess:
    def __init__(self, session_dir, image):
        self.dir = session_dir
        self.image = image
        self.proc = None

    def start(self):
        args = [config.QEMU] + [a % self.image if "%s" in a else a for a in ARGS]
        self.proc = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 8
        while time.time() < deadline and self.proc.poll() is None:
            if _port_open(config.GDB_PORT):
                return
            time.sleep(0.1)
        raise RuntimeError("QEMU 没有起来")

    @property
    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def stop(self):
        if self.proc is None:
            return
        if self.alive:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=2)
        wait_free()


def free_ports():
    """Kill whatever still owns our fixed ports (stale process from a crash)."""
    for port in (config.GDB_PORT, config.SERIAL_PORT, config.RFB_PORT):
        for pid in _owners(port):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True)


def _owners(port):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-NetTCPConnection -LocalPort %d -ErrorAction SilentlyContinue)."
         "OwningProcess | Sort-Object -Unique" % port],
        capture_output=True, text=True,
    )
    return [int(x) for x in result.stdout.split() if x.strip().isdigit()]


def wait_free(ports=None, timeout=4.0):
    ports = ports or (config.GDB_PORT, config.SERIAL_PORT, config.RFB_PORT)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not any(_port_open(p) for p in ports):
            return True
        time.sleep(0.1)
    return False


def _port_open(port):
    import socket
    try:
        socket.create_connection((config.HOST, port), 0.2).close()
        return True
    except OSError:
        return False
