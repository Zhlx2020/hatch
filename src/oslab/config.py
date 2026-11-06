"""All tunables and paths. Nothing else may hardcode these."""
import os
import shutil

HOST = "127.0.0.1"
PORT = 8799
LOCK_PORT = 5912
RFB_PORT = 5901
GDB_PORT = 5913
SERIAL_PORT = 5914
VNC_HOST_PORT = 1
BACKEND = "qemu"

HEADERBAR = 32
STATUSBAR = 20
FRAME_MS = 60
BOOT_TIMEOUT = 300

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(ROOT))
ASSETS = os.path.join(ROOT, "assets")
UI_DIR = os.path.join(ASSETS, "ui")
WORKSPACE = os.path.join(PROJECT, "workspace")
RUN_DIR = os.path.join(PROJECT, ".run")
_BIN = os.path.join(PROJECT, ".work", "w64", "w64devkit", "bin")
_ASM = os.path.join(PROJECT, "..", "osdev-lab", "tools", "nasm-3.02")

SENTINEL = "OSLAB_SYNC"


def _tool(name, env, *hints):
    """按 环境变量 → 随项目放的工具 → PATH 顺序找外装命令。

    硬编码的提示目录只是便利：换台机器时用环境变量或 PATH 覆盖即可。
    """
    if os.environ.get(env):
        return os.environ[env]
    for hint in hints:
        if hint and os.path.exists(hint):
            return hint
    return shutil.which(name) or (hints[0] if hints else name)


NASM = _tool("nasm", "HATCH_NASM", os.path.join(_ASM, "nasm.exe"))
OBJDUMP = _tool("objdump", "HATCH_OBJDUMP", os.path.join(_BIN, "objdump.exe"))
QEMU = _tool("qemu-system-i386", "HATCH_QEMU", r"C:\Program Files\qemu\qemu-system-i386.exe")
C_GCC = _tool("gcc", "HATCH_GCC", os.path.join(_BIN, "gcc.exe"))
C_LD = _tool("ld", "HATCH_LD", os.path.join(_BIN, "ld.exe"))
C_OBJCOPY = _tool("objcopy", "HATCH_OBJCOPY", os.path.join(_BIN, "objcopy.exe"))

BOCHS = _tool("bochs", "HATCH_BOCHS", r"C:\software\Bochs-3.0\bochs.exe")
BOCHS_SHARE = r"C:\software\Bochs-3.0"
