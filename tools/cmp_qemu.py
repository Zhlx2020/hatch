"""Head-to-head: QEMU (gdbstub + vnc) vs Bochs (pipe debugger + rfb).

Measures only the things the IDE depends on: async break-in, register/memory
access, breakpoints, screen transport quality, port freedom, multi-viewer.
"""
import os
import socket
import struct
import subprocess
import sys
import threading
import time

QEMU = r"C:\Program Files\qemu\qemu-system-i386.exe"
BOCHS = r"C:\software\Bochs-3.0\bochs.exe"
SHARE = r"C:\software\Bochs-3.0"
D = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(D, "cmp")
GDB_PORT = 1234
VNC_PORT = 5901


def boot_image():
    os.makedirs(WORK, exist_ok=True)
    img = os.path.join(WORK, "b.img")
    data = bytearray(b"\xeb\xfe" * 256)
    data[510:512] = b"\x55\xaa"
    with open(img, "wb") as fh:
        fh.write(bytes(data))
    return img


def rsp_read(sock):
    data = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            return data
        data += chunk
        if len(data) > 2 and data.endswith(b"#") is False:
            body = data.split(b"#")[0]
            if data.count(b"#") and len(data) >= data.index(b"#") + 3:
                return data


def main():
    img = boot_image()
    proc = subprocess.Popen(
        [QEMU, "-drive", "file=%s,if=floppy,format=raw" % img, "-boot", "a",
         "-m", "32", "-display", "vnc=127.0.0.1:1", "-s", "-S",
         "-monitor", "none", "-serial", "none"],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(2.5)

    print("alive:", proc.poll() is None)

    vnc = socket.create_connection(("127.0.0.1", VNC_PORT), 4)
    vnc.settimeout(4)
    print("vnc banner:", vnc.recv(12))
    vnc.send(b"RFB 003.008\n")
    types = vnc.recv(64)
    print("security types head:", types[:6])
    vnc.send(b"\x01")
    time.sleep(0.2)
    print("result:", vnc.recv(4))
    vnc.send(b"\x01")
    head = vnc.recv(24 + 32)
    w, h = struct.unpack(">HH", head[:4])
    bpp, depth, big, true = head[4], head[5], head[6], head[7]
    rmax, gmax, bmax = struct.unpack(">HHH", head[8:14])
    rs, gs, bs = head[14], head[15], head[16]
    print("screen: %dx%d bpp=%d depth=%d true=%d max=%d/%d/%d shift=%d/%d/%d"
          % (w, h, bpp, depth, true, rmax, gmax, bmax, rs, gs, bs))

    second = socket.create_connection(("127.0.0.1", VNC_PORT), 4)
    second.settimeout(4)
    try:
        print("second viewer banner:", second.recv(12)[:12])
    except socket.timeout:
        print("second viewer banner: TIMEOUT")

    gdb = socket.create_connection(("127.0.0.1", GDB_PORT), 4)
    gdb.settimeout(4)
    time.sleep(0.3)

    gdb.send(b"?")
    print("regs reply:", rsp_read(gdb)[:80])

    gdb.send(b"m7c00,8")
    print("mem read:", rsp_read(gdb)[:40])

    gdb.send(b"Z0,7c00,1")
    print("set bp:", rsp_read(gdb)[:20])

    gdb.send(b"c")
    time.sleep(1.0)
    gdb.send(b"\x03")
    try:
        stop = rsp_read(gdb)
        print("async break stop reply:", stop[:60])
    except socket.timeout:
        print("async break stop reply: TIMEOUT")

    gdb.send(b"g")
    try:
        regs = rsp_read(gdb)
        print("g reply len:", len(regs))
    except socket.timeout:
        print("g reply: TIMEOUT")

    for sock in (gdb, vnc, second):
        try:
            sock.close()
        except OSError:
            pass
    proc.kill()


main()
