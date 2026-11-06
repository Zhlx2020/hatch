"""QEMU backend over the gdb remote protocol."""
import re

from ... import config
from ...core.errors import BackendError
from ...services import disasm
from .process import QemuProcess
from .rsp import Rsp

# i386 'g' packet layout: 16 little-endian 32-bit words, in this order.
REGS = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi",
        "eip", "eflags", "cs", "ss", "ds", "es", "fs", "gs"]
INDEX = {name: i for i, name in enumerate(REGS)}
SEGMENTS = ("cs", "ss", "ds", "es", "fs", "gs")


class QemuBackend:
    def __init__(self, session_dir, image, tune=None):
        self._proc = QemuProcess(session_dir, image, tune)
        self._image = image
        self._rsp = None
        self.on_stop = None            # 会话注册：状态是被推上来的
        self._lines = []
        self._att = []

    # lifecycle ------------------------------------------------------
    def start(self):
        self._proc.start()
        self._rsp = Rsp(config.HOST, config.GDB_PORT)
        self._lines = disasm.load(self._image, "intel")
        self._att = disasm.load(self._image, "att")
        # 会话在 start() 之后才挂回调，这里转发一层保证拿到最新的
        self._rsp.on_stop = lambda body: self.on_stop and self.on_stop(body)
        self._rsp.stop_reason()

    def stop(self):
        if self._rsp:
            self._rsp.close()
            self._rsp = None
        self._proc.stop()

    @property
    def alive(self):
        return self._proc.alive

    # execution ------------------------------------------------------
    def cont(self):
        """发完就回；真停下来由 on_stop 回调通知。"""
        self._need().cont()

    def step(self):
        self._need().step()
        return self.registers()

    def step_over(self):
        """No disassembler in the stub: a plain step is honest here."""
        return self.step()

    def pause(self):
        self._need().interrupt()
        return "stopped"

    def reset(self):
        self._need().stop_reason()
        self._need().write_reg(self._index("eip"), 0xFFF0)
        self._need().cont()

    # registers ------------------------------------------------------
    def _index(self, name):
        if name not in INDEX:
            raise BackendError("没有寄存器 %s" % name)
        return INDEX[name]

    def _raw_regs(self):
        raw = self._need().read_regs()
        if raw.startswith("E"):
            raise BackendError("取寄存器失败")
        words = []
        for i in range(0, min(len(raw), 128), 8):
            words.append(int.from_bytes(bytes.fromhex(raw[i:i + 8]), "little"))
        return words

    def registers(self):
        words = self._raw_regs()
        lines = []
        for name in REGS:
            value = words[INDEX[name]]
            if name in SEGMENTS:
                lines.append("%s : %04x" % (name, value & 0xFFFF))
            elif name == "eflags":
                lines.append("eflags: 0x%08x" % value)
            else:
                lines.append("%s: 0x%08x" % (name, value))
        return "\n".join(lines)

    def reg_map(self):
        """Structured registers for the detail panel."""
        words = self._raw_regs()
        out = {}
        for name in REGS:
            value = words[INDEX[name]]
            out[name] = value & (0xFFFF if name in SEGMENTS else 0xFFFFFFFF)
        return out

    def set_reg(self, name, value):
        index = self._index(name)
        word = value & (0xFFFF if name in SEGMENTS else 0xFFFFFFFF)
        self._need().write_reg(index, word)
        return word

    def eip(self):
        return self._raw_regs()[INDEX["eip"]]

    def _reg_value(self, name):
        return self._raw_regs()[self._index(name)]

    # memory ---------------------------------------------------------
    def read_mem(self, addr, count):
        return self._need().read_mem(addr, count)

    def disassemble(self, addr, count=8, syntax="intel"):
        return disasm.around(self._pick(syntax), addr, count)

    def mem_rows(self, addr, count):
        data = self.read_mem(addr, count)
        rows = []
        for offset in range(0, len(data), 16):
            chunk = data[offset:offset + 16]
            rows.append({
                "addr": "%08x" % (addr + offset),
                "hex": ["%02x" % b for b in chunk],
                "text": "".join(chr(b) if 32 <= b < 127 else "." for b in chunk),
            })
        return rows

    def disasm_rows(self, addr, count, syntax="intel"):
        return disasm.rows(self._pick(syntax), addr, count)

    def _pick(self, syntax):
        return self._att if syntax == "att" else self._lines

    def hexdump(self, addr, count):
        try:
            data = self.read_mem(addr, count)
        except BackendError as exc:
            return str(exc)
        rows = []
        for offset in range(0, len(data), 16):
            chunk = data[offset:offset + 16]
            hexpart = " ".join("%02x" % b for b in chunk)
            text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            rows.append("%08x  %-47s  %s" % (addr + offset, hexpart, text))
        return "\n".join(rows)

    def dump_stack(self, esp):
        value = int(esp, 16) if isinstance(esp, str) else int(esp)
        return self.hexdump(value & 0xFFFFFFFF, 64)

    # breakpoints ----------------------------------------------------
    def break_at(self, addr):
        self._need().breakpoint(addr, True)

    def unbreak(self, addr):
        self._need().breakpoint(addr, False)

    def break_list(self):
        return ""

    # misc -----------------------------------------------------------
    def page_walk(self, addr):
        return ""

    def gdt(self):
        return ""

    def idt(self):
        return ""

    def log_tail(self, n=20):
        return []

    def _need(self):
        if not self._rsp:
            raise BackendError("调试通道未建立")
        return self._rsp
