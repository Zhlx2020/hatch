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
_TOOLS = os.path.join(PROJECT, ".work", "tools")
_BIN = os.path.join(_TOOLS, "w64devkit", "bin")
_ASM = os.path.join(_TOOLS, "nasm-2.16.03")

SENTINEL = "OSLAB_SYNC"


def _tool(name, env, *hints):
    """按 环境变量 → 项目自带的工具 → PATH → 旧目录 顺序找外装命令。

    环境变量写错了（指向不存在的文件）就当没写，免得一个笔误把能用的工具遮住。
    项目自带的那些由 services/toolchain.py 下载到 .work/tools，
    所以用户机器上什么都不用先装。
    """
    override = os.environ.get(env)
    if override and os.path.exists(override):
        return override
    managed = os.path.join(PROJECT, ".work", "tools")
    for hint in hints:
        if hint and hint.startswith(managed) and os.path.exists(hint):
            return hint
    found = shutil.which(name)
    if found:
        return found
    for hint in hints:
        if hint and os.path.exists(hint):
            return hint
    return hints[0] if hints else name


NASM = _tool("nasm", "HATCH_NASM", os.path.join(_ASM, "nasm.exe"))
OBJDUMP = _tool("objdump", "HATCH_OBJDUMP", os.path.join(_BIN, "objdump.exe"))
QEMU = _tool("qemu-system-i386", "HATCH_QEMU",
             os.path.join(_TOOLS, "qemu", "qemu-system-i386.exe"),
             r"C:\Program Files\qemu\qemu-system-i386.exe")
C_GCC = _tool("gcc", "HATCH_GCC", os.path.join(_BIN, "gcc.exe"))
C_LD = _tool("ld", "HATCH_LD", os.path.join(_BIN, "ld.exe"))
C_OBJCOPY = _tool("objcopy", "HATCH_OBJCOPY", os.path.join(_BIN, "objcopy.exe"))

BOCHS = _tool("bochs", "HATCH_BOCHS", r"C:\software\Bochs-3.0\bochs.exe")
BOCHS_SHARE = r"C:\software\Bochs-3.0"
