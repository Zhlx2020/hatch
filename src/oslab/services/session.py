"""One session: owns the backend, arbitrates every action, serves snapshots."""
import os
import re
import socket
import threading
from contextlib import contextmanager
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
from . import build, linemap, project, settings, sourcemap, workspace
from .serial import SerialBuffer

REG_LINE = re.compile(r"^(eip|rip):\s*(?:0x)?([0-9a-fA-F]+)")
ANY_REG = re.compile(r"^([a-z]+):\s*(?:0x)?([0-9a-fA-F]+)", re.M)


def parse_reg(text, name):
    """从一份 registers() 输出里取某个名字的值，取不到给 0。"""
    for found, value in ANY_REG.findall(text or ""):
        if found.lower() == name:
            return value
    return "0"


class Session:
    def __init__(self):
        self.arbiter = Arbiter()
        self.dir = make_qemu_dir()
        self.image = os.path.join(self.dir, "boot.img")
        self.elf = os.path.join(self.dir, "kernel.elf")
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
        self.held = False
        self.stale = 0.0
        self.snaplog = bool(os.environ.get("HATCH_SNAPLOG"))
        self.log_fh = None
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
                self.tune = settings.with_project(settings.load(), name)
                self.tune = settings.layer(self.tune, self._project_qemu(name))
                for disk in self.tune["qemu"].get("disks") or []:
                    if not os.path.isfile(workspace.full(disk["path"])):
                        raise OsLabError("附加盘不存在：%s" % disk["path"])
                self.backend = QemuBackend(self.dir, self.image, self.tune)
                self.backend.start()
                self.backend.on_stop = self._on_stop
                if not self._await_ready():
                    raise OsLabError("模拟器未就绪")
                # 手动断点只在“同一份文件重跑”时留着；换了程序地址就对不上了
                kept = sorted(self.bps) if self.file == name else []
                self.bps.clear()
                # 红点在构建后才有地址：先写断点，再放行，避免跑过头
                placed = []
                for line in lines or []:
                    addr = linemap.lookup(self.line_map, name, int(line))
                    if addr:
                        self.add_breakpoint(addr)
                        placed.append("%08x" % addr)
                for addr in kept:
                    self.add_breakpoint(addr)
                self.serial = SerialBuffer(None)
                deadline = time.time() + 2.0
                while time.time() < deadline and not self.serial.connected:
                    time.sleep(0.02)
                self.cursor = 0
                self.file = name
                self.arbiter.to(state.RUNNING, "booted")
                # 默认一路放行：有红点就停在第一个红点。pause_at_entry 置 false 才真的停在复位向量
                if self.tune["run"].get("pause_at_entry", True) or placed:
                    self.backend.cont()
                    for _ in range(30):
                        if self.arbiter.state != state.RUNNING:
                            break
                        time.sleep(0.01)

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

    def _project_qemu(self, name):
        """工程清单里的 [qemu]：跟着工程走，不靠用户设置里那份全局的。"""
        try:
            directory = project.find(name)
            if not directory:
                return {}
            return project.load(directory).get("qemu") or {}
        except OsLabError:
            return {}

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
        self.cache = {}          # 上一台机器的寄存器和反汇编不许带到下一个程序
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
        backend = self._need_backend()
        stuck = None
        # 停在断点上再继续，先把那条 int3 迈过去，不然一 cont 立刻又撞回同一个点。
        if self.bps:
            try:
                here = backend.eip() & 0xFFFFFFFF
            except (BackendError, OSError, TimeoutError):
                here = None
            if here in self.bps:
                stuck = here
        self.arbiter.to(state.RUNNING, "cont")     # 先立状态，回调才有处落脚
        if stuck is not None:
            backend.unbreak(stuck)
            try:
                backend.step()
            finally:
                backend.break_at(stuck)
            self.arbiter.to(state.RUNNING, "cont")  # step 的停机回调把状态压回了 STOPPED
        backend.cont()
        return self.arbiter.state

    def _on_stop(self, packet):
        """gdbstub 推上来的停机（断点、暂停、结束）。跑在读线程里，只碰状态机。"""
        try:
            with open(".run/stop.log", "a") as fh:
                fh.write("%.3f %s %s\n" % (time.time(), packet[:12], self.arbiter.state))
        except OSError:
            pass
        if self.arbiter.state not in (state.RUNNING, state.BOOTING):
            return
        try:
            self.arbiter.to(state.STOPPED, "hit" if packet[:1] == b"T" else "exit")
        except BadTransition:
            pass

    def pause(self):
        with self._guard:          # 等补读那一组走完，状态已settle
            self.arbiter.guard(state.RUNNING, state.STOPPED)
            if self.arbiter.state == state.STOPPED:
                return "paused"
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
    @contextmanager
    def _keep_running(self):
        """读寄存器或内存会让 QEMU 停下，本来在跑就得放它回去。

        不然每次面板补读都会把客户机按在原地：画面不刷新，键盘也读不到。
        """
        # 一次只放一组“按停→读→放开”进去，否则几路轮询会把 gdb 流搅乱。
        with self._guard:
            resume = self.arbiter.state == state.RUNNING and self.backend is not None \
                and self.backend.alive
            if resume:
                # 运行中的读不会被 gdbstub 立刻回答，得先按停（0x03）再读。
                try:
                    self.backend.pause()
                except (BackendError, OSError):
                    resume = False
            self.held = resume
            try:
                yield
            finally:
                # 按停是我们自己发的，放开也由我们负责（状态已被回调改成 stopped）
                if resume:
                    self._resume()
                self.held = False

    def _resume(self):
        try:
            self.arbiter.to(state.RUNNING, "resume")
            self.backend.cont()
        except (BackendError, BadTransition, OSError):
            pass

    def reg_detail(self):
        with self._keep_running():
            backend = self._need_backend()
            return {"regs": backend.reg_map(), "eip": "%08x" % backend.eip(),
                    "state": self.arbiter.state}

    def set_reg(self, name, value):
        backend = self._need_backend()
        with self._keep_running():
            backend.set_reg(name, value)
            return "%08x" % backend._reg_value(name)

    def mem_rows(self, addr, count=256):
        with self._keep_running():
            rows = self._need_backend().mem_rows(addr & 0xFFFFFFF0, min(int(count), 1024))
        return {"addr": "%08x" % addr, "rows": rows}

    def line_addr(self, path, line):
        """Address of a source line from the last build, or 0."""
        return linemap.lookup(self.line_map, path, int(line))

    def disasm_rows(self, addr, count=32, syntax="intel"):
        with self._keep_running():
            rows = self._need_backend().disasm_rows(addr, min(int(count), 256), syntax)
            return {"addr": "%08x" % addr, "rows": rows, "eip": "%08x" % self.eip()}

    def snapshot(self):
        if not self.backend or not self.backend.alive:
            return {"state": self.arbiter.state, "error": self.last_error, "file": self.file}
        live = self.arbiter.state
        if self.held and live == state.STOPPED:
            live = state.RUNNING       # 临时按停补读期间，对外仍算运行中
        if live in (state.RUNNING, state.BOOTING):
            text, cursor = self.serial.since(self.cursor) if self.serial else ("", 0)
            if self.snaplog:
                self._log("%r cur=%s new=%s buf=%s" % (
                    text[:20], self.cursor, cursor,
                    len(self.serial.tail()) if self.serial else -1))
            self.cursor = cursor
            # 运行中不碰 gdb：画面和串口照常，寄存器停在上一帧的值
            return dict(self.cache, state=live, file=self.file,
                        serial=text, error=self.last_error)
        return self._snapshot()

    def _snapshot(self):
        data = dict(self.cache)
        for key in ("state", "error"):
            data.pop(key, None)
        try:
            with self._keep_running():
                regs = self.backend.registers()          # 一次读全，下面都从这份里取
                eip = int(parse_reg(regs, "eip"), 16)
                data["eip"] = "%08x" % eip
                data["regs"] = regs
                data["disasm"] = self.backend.disassemble(eip, 8)
                data["mem"] = self.backend.hexdump(eip, 128)
                esp = int(parse_reg(regs, "esp"), 16)
                data["stack"] = self.backend.dump_stack(esp)
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

    def _log(self, line):
        try:
            if self.log_fh is None:
                self.log_fh = open(".run/ser.log", "a", buffering=1)
            self.log_fh.write(line + "\n")
        except OSError:
            self.log_fh = None

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
        with self._keep_running():
            return self._need_backend().hexdump(addr, count)

    def tables(self):
        with self._keep_running():
            return {"gdt": self._need_backend().gdt(), "idt": self._need_backend().idt()}
