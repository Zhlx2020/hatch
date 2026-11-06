"""All tunables and paths. Nothing else may hardcode these."""
import os

BOCHS = r"C:\software\Bochs-3.0\bochs.exe"
BOCHS_SHARE = r"C:\software\Bochs-3.0"
NASM = r"C:\Users\zlx\Documents\deepseek-harness\default-workspace\osdev-lab\tools\nasm-3.02\nasm.exe"
OBJDUMP = r"C:\Users\zlx\Documents\deepseek-harness\default-workspace\oslab\.work\w64\w64devkit\bin\objdump.exe"
QEMU = r"C:\Program Files\qemu\qemu-system-i386.exe"
_W64 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".work", "w64", "w64devkit", "bin")
C_GCC = os.path.abspath(os.path.join(_W64, "gcc.exe"))
C_LD = os.path.abspath(os.path.join(_W64, "ld.exe"))
C_OBJCOPY = os.path.abspath(os.path.join(_W64, "objcopy.exe"))

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

SENTINEL = "OSLAB_SYNC"
