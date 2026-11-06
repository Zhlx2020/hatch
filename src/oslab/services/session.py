"""One session: owns the backend, arbitrates every action, serves snapshots."""
import os
import re
import socket
import threading
import time
import traceback
import time

from .. import config
from ..backend.bochs.adapter import BochsBackend
from ..backend.bochs.process import make_session_dir
from ..backend.qemu.adapter import QemuBackend
from ..backend.qemu.process import make_session_dir as make_qemu_dir, wait_free
from ..core import state
from ..core.arbiter import Arbiter
from ..core.errors import BackendError, BadTransition, OsLabError
from ..display.rfb import RfbSource
from ..display.vnc import VncSource
from . import build, linemap, settings, sourcemap, workspace
from .serial import SerialBuffer

REG_LINE = re.compile(r"^(eip|rip):\s*(?:0x)?([0-9a-fA-F]+)")


class Session:
    def __init__(self):
        self.arbiter = Arbiter()
        self.dir = make_qemu_dir()
        self.image = os.path.join(self.dir, "boot.img")
        self.backend = None
        self.serial = None
        self.source = VncSource()
        self.file = ""
        self._guard = threading.RLock()
        self.last_error = ""
        self.cursor = 0
        self.bps = set()
        self.source_map = {}
        self.line_map = {}
        self.want_run = False
        self.cache = {}
        self.stale = 0.0
        self.filling = False

    # lifecycle ------------------------------------------------------
    def prepare(self):
        first = workspace.entry_file()
        if first:
            try:
                self.run_file(first)
            except Exception:
                pass

    def run_file(self, name, lines=None):
        if not name:
            raise OsLabError("没有选中文件")
        text = workspace.read(name)
        return self.build_and_boot(text, name, lines)

    def build_only(self, text, name=""):
        """构建但不启动：按钮设成“只构建”时走这里。"""
        with self._guard:
            self.arbiter.to(state.BOOTING, "build")
            try:
                built, line_map = build.build(text, name, self.image)
                self.line_map = line_map or linemap.from_listing(self.image, name)
                self.file = name
                self.last_error = ""
                self.arbiter.to(state.IDLE, "built")
            except Exception as exc:
                self.last_error = str(exc) or exc.__class__.__name__
                try:
                    self.arbiter.to(state.FAULTED, self.last_error)
                except BadTransition:
                    pass
                raise
            return {"state": self.arbiter.state, "file": name, "built": True}

    def build_and_boot(self, text, name="", lines=None):
        with self._guard:
            if self.arbiter.state == state.RUNNING:
                try:
                    self._need_backend().pause()
                    self.arbiter.to(state.STOPPED, "pre-run")
                except (BackendError, BadTransition, OSError, TimeoutError):
                    pass
            self.arbiter.to(state.BOOTING, "assemble")
            try:
                built, line_map = build.build(text, name, self.image)
                self.source_map = sourcemap.load(self.image)
                self.line_map = line_map or linemap.from_listing(self.image, name)
                current_lines = self.line_map.get(workspace.safe(name)) or {}
                if current_lines:      # C 的地址反查也走同一张表
                    self.source_map = {addr: line for line, addr in current_lines.items()}
                self._teardown()
                self.tune = settings.load()
                self.backend = QemuBackend(self.dir, self.image, self.tune)
                self.backend.start()
                if not self._await_ready():
                    raise OsLabError("模拟器未就绪")
                self.bps.clear()
                # 红点在构建后才有地址：先写断点，再放行，避免跑过头
                placed = []
                for line in lines or []:
                    addr = linemap.lookup(self.line_map, name, int(line))
                    if addr:
                        self.add_breakpoint(addr)
                        placed.append("%08x" % addr)
                self.serial = SerialBuffer(None)
                deadline = time.time() + 2.0
                while time.time() < deadline and not self.serial.connected:
                    time.sleep(0.02)
                self.cursor = 0
                self.file = name
                if self.tune["run"]["pause_at_entry"]:
                    hit = self.backend.cont()
                else:
                    hit = "stopped"       # 停在入口等用户放行
                if hit == "stopped":
                    self.arbiter.to(state.STOPPED, "hit")
                else:
                    self.arbiter.to(state.RUNNING, "booted")

                self.last_error = ""
                self.placed_bps = placed
            except Exception as exc:
                traceback.print_exc()
                self.last_error = str(exc) or exc.__class__.__name__
                try:
                    self.arbiter.to(state.FAULTED, str(exc))
                except BadTransition:
                    pass
                raise
            return {"state": self.arbiter.state, "file": name}

    def _run_when_online(self, timeout=20.0):
        """Bochs blocks until an rfb client finishes the handshake; only then can
        the machine actually run, so the continue has to wait for the pump."""
        end = time.time() + timeout
        while time.time() < end:
            if not self.backend or not self.backend.alive:
                return
            if self.source.online:
                try:
                    if self.want_run:
                        self.backend.cont()
                except Exception:
                    pass
                return
            time.sleep(0.1)

    def _teardown(self):
        if self.backend:
            try:
                self.backend.stop()
            except Exception:
                pass
            self.backend = None
        if self.serial:
            self.serial.close()
            self.serial = None
        wait_free()

    def _await_ready(self, timeout=8.0):
        return self.backend.alive

    def stop(self):
        with self._guard:
            self._teardown()
            try:
                self.arbiter.to(state.IDLE, "stopped")
            except BadTransition:
                pass

    def _need_backend(self):
        if not self.backend or not self.backend.alive:
            raise OsLabError("机器没在跑，先点运行")
        return self.backend

    # control --------------------------------------------------------
    def cont(self):
        self.arbiter.guard(state.STOPPED, state.RUNNING)
        result = self._need_backend().cont()
        if result == "stopped":
            self.arbiter.to(state.STOPPED, "hit")
        else:
            self.arbiter.to(state.RUNNING, "cont")
        return result

    def pause(self):
        self.arbiter.guard(state.RUNNING)
        self._need_backend().pause()
        self.arbiter.to(state.STOPPED, "pause")
        return "paused"

    def step(self):
        self.arbiter.guard(state.RUNNING, state.STOPPED)
        out = self._need_backend().step()
        self.arbiter.to(state.STOPPED, "step")
        return out

    def step_over(self):
        self.arbiter.guard(state.RUNNING, state.STOPPED)
        out = self._need_backend().step_over()
        self.arbiter.to(state.STOPPED, "step-over")
        return out

    def reset(self):
        self.arbiter.guard(state.RUNNING, state.STOPPED)
        self._need_backend().reset()
        self.arbiter.to(state.RUNNING, "reset")

    def add_breakpoint(self, addr):
        self._need_backend().break_at(addr)
        self.bps.add(addr)
        return "%08x" % addr

    def remove_breakpoint(self, addr):
        self._need_backend().unbreak(addr)
        self.bps.discard(addr)
        return "%08x" % addr

    def breakpoints(self):
        return ["%08x" % a for a in sorted(self.bps)]

    def serial_tail(self):
        return self.serial.tail() if self.serial else ""

    # observation ----------------------------------------------------
    def reg_detail(self):
        backend = self._need_backend()
        return {"regs": backend.reg_map(), "eip": "%08x" % backend.eip(),
                "state": self.arbiter.state}

    def set_reg(self, name, value):
        backend = self._need_backend()
        backend.set_reg(name, value)
        return "%08x" % backend._reg_value(name)

    def mem_rows(self, addr, count=256):
        rows = self._need_backend().mem_rows(addr & 0xFFFFFFF0, min(int(count), 1024))
        return {"addr": "%08x" % addr, "rows": rows}

    def line_addr(self, path, line):
        """Address of a source line from the last build, or 0."""
        return linemap.lookup(self.line_map, path, int(line))

    def disasm_rows(self, addr, count=32, syntax="intel"):
        rows = self._need_backend().disasm_rows(addr, min(int(count), 256), syntax)
        return {"addr": "%08x" % addr, "rows": rows, "eip": "%08x" % self.eip()}

    def snapshot(self):
        if not self.backend or not self.backend.alive:
            return {"state": self.arbiter.state, "error": self.last_error, "file": self.file}
        if self.arbiter.state in (state.RUNNING, state.BOOTING):
            text, cursor = self.serial.since(self.cursor) if self.serial else ("", 0)
            self.cursor = cursor
            data = dict(self.cache, state=self.arbiter.state, file=self.file,
                        serial=text, error=self.last_error)
            if self.arbiter.state == state.BOOTING:
                # 启动过程里也要看得见机器：此时客户机停在复位点，读一下无害。
                data.update(self._snapshot())
            elif time.monotonic() - self.stale > 1.5 and not self.filling:
                # 运行中低频补读一次，面板不至于一直是空的
                self.filling = True
                try:
                    data.update(self._snapshot())
                finally:
                    self.filling = False
            return data
        return self._snapshot()

    def _snapshot(self):
        data = dict(self.cache)
        for key in ("state", "error"):
            data.pop(key, None)
        try:
            eip = self.eip()
            data["eip"] = "%08x" % eip
            data["regs"] = self.backend.registers()
            data["disasm"] = self.backend.disassemble(eip, 8)
            data["mem"] = self.backend.hexdump(eip, 128)
            data["stack"] = self.backend.dump_stack(self._reg("esp"))
            data["line"] = sourcemap.line_at(self.source_map, eip)
        except Exception as exc:            # a timeout must not lose the view
            data["error"] = "读取超时：%s" % exc
        data["state"] = self.arbiter.state
        data["file"] = self.file
        if self.last_error:                # 真正的失败原因优先于偶发读超时
            data["error"] = self.last_error
        self.stale = time.monotonic()
        data["bps"] = self.breakpoints()
        data["serial"] = self.serial.since(self.cursor)[0] if self.serial else ""
        self.cache = {k: v for k, v in data.items()
                      if k not in ("serial", "state", "error")}
        return data

    def eip(self):
        return int(self._reg("eip"), 16)

    def _reg(self, name):
        out = self._need_backend().registers()
        for line in out.splitlines():
            match = REG_LINE.match(line.strip().lower())
            if match and match.group(1) == name:
                return match.group(2)
        return "0"

    def dump_memory(self, addr, count):
        return self._need_backend().hexdump(addr, count)

    def tables(self):
        return {"gdt": self._need_backend().gdt(), "idt": self._need_backend().idt()}
