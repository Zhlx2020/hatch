"""High level debugger semantics on top of the pipe protocol."""
import re

from ...core.errors import BackendError
from .process import BochsProcess

BYTES = re.compile(r"0x([0-9a-fA-F]{2})\b")
INSN_BYTES = re.compile(r"^\s*[0-9a-f]{4,16}:\s+((?:[0-9a-f]{2}\s)+)")
EIP = re.compile(r"^(?:eip|rip):\s*([0-9a-fA-F]+)", re.MULTILINE)


class BochsBackend:
    def __init__(self, session_dir, image):
        self._proc = BochsProcess(session_dir, image)

    # lifecycle ------------------------------------------------------
    def start(self):
        self._proc.start()

    def stop(self):
        self._proc.stop()

    @property
    def alive(self):
        return self._proc.alive

    # execution ------------------------------------------------------
    def cont(self):
        self._proc.protocol.run("c", timeout=1.2)

    def step(self):
        return self._proc.protocol.run("s")

    def step_over(self):
        """Run to the next instruction by breaking just past the current one."""
        here = self.eip()
        raw = self.disassemble(here, 1)
        size = 1
        for line in raw.splitlines():
            match = INSN_BYTES.match(line)
            if match:
                size = len(match.group(1).split())
                break
        target = here + size
        self.break_at(target)
        self.cont()
        self.unbreak(target)
        return self.registers()

    def reset(self):
        self._proc.protocol.run("reset hard")

    # breakpoints ----------------------------------------------------
    def break_at(self, addr):
        self._proc.protocol.run("pb 0x%x" % addr)

    def unbreak(self, addr):
        self._proc.protocol.run("delete 0x%x" % addr)

    def break_list(self):
        return self._proc.protocol.run("blist")

    # observation ----------------------------------------------------
    def registers(self):
        return self._proc.protocol.run("r")

    def eip(self):
        match = EIP.search(self.registers())
        return int(match.group(1), 16) if match else 0

    def disassemble(self, addr, count=8):
        return self._proc.protocol.run("u /%d 0x%x" % (count, addr))

    def read_mem(self, addr, count):
        raw = self._proc.protocol.run("xp /%db 0x%x" % (count, addr))
        return bytes(int(v, 16) for v in BYTES.findall(raw))

    def hexdump(self, addr, count):
        """Raw xp output, already formatted by Bochs."""
        return self._proc.protocol.run("xp /%dxb 0x%x" % (count, addr))

    def dump_stack(self, esp_hex):
        return self.hexdump(int(esp_hex, 16) & 0xFFFFFFFF, 64)

    def page_walk(self, addr):
        return self._proc.protocol.run("page 0x%x" % addr)

    def gdt(self):
        return self._proc.protocol.run("info gdt")

    def idt(self):
        return self._proc.protocol.run("info idt")

    def log_tail(self, n=20):
        return self._proc.protocol.tail(n)

    def require_alive(self):
        if not self.alive:
            raise BackendError("Bochs 已退出")
