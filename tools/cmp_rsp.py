"""Raw RSP check against QEMU gdbstub, with proper $...#cs framing."""
import os
import socket
import subprocess
import time

QEMU = r"C:\Program Files\qemu\qemu-system-i386.exe"
D = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(D, "cmp")


def frame(body):
    return b"$" + body + b"#%02x" % (sum(body) & 0xFF)


def ask(sock, body, label):
    sock.send(frame(body))
    time.sleep(0.4)
    try:
        print(label, "->", sock.recv(512)[:90])
    except socket.timeout:
        print(label, "-> TIMEOUT")


def main():
    os.makedirs(WORK, exist_ok=True)
    img = os.path.join(WORK, "b.img")
    data = bytearray(b"\xeb\xfe" * 256)
    data[510:512] = b"\x55\xaa"
    with open(img, "wb") as fh:
        fh.write(bytes(data))
    proc = subprocess.Popen(
        [QEMU, "-drive", "file=%s,if=floppy,format=raw" % img, "-boot", "a",
         "-m", "32", "-display", "none", "-gdb", "tcp:127.0.0.1:1235", "-S",
         "-monitor", "none", "-serial", "none"],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(2.0)
    print("alive:", proc.poll() is None)

    gdb = socket.create_connection(("127.0.0.1", 1235), 4)
    gdb.settimeout(3.0)
    time.sleep(0.3)

    ask(gdb, b"?", "stop reason")
    ask(gdb, b"g", "registers")
    ask(gdb, b"m7c00,8", "mem")
    ask(gdb, b"Z0,7c00,1", "bp")

    gdb.send(frame(b"c"))
    time.sleep(1.2)
    gdb.send(b"\x03")
    try:
        print("async break ->", gdb.recv(512)[:90])
    except socket.timeout:
        print("async break -> TIMEOUT")

    ask(gdb, b"g", "registers after break")

    gdb.close()
    proc.kill()


main()
