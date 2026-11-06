"""Read QEMU's target.xml to learn the register order for 'g' replies."""
import os
import socket
import subprocess
import time

QEMU = r"C:\Program Files\qemu\qemu-system-i386.exe"
D = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(D, "cmp")


def frame(body):
    return b"$" + body + b"#%02x" % (sum(body) & 0xFF)


def main():
    os.makedirs(WORK, exist_ok=True)
    img = os.path.join(WORK, "b.img")
    proc = subprocess.Popen(
        [QEMU, "-drive", "file=%s,if=floppy,format=raw" % img, "-boot", "a",
         "-m", "32", "-display", "none", "-gdb", "tcp:127.0.0.1:1236", "-S",
         "-monitor", "none", "-serial", "none"],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(2.0)
    gdb = socket.create_connection(("127.0.0.1", 1236), 4)
    gdb.settimeout(3.0)
    time.sleep(0.3)

    offset = 0
    while True:
        gdb.send(frame(b"qXfer:features:read:target.xml:%x,fff" % offset))
        time.sleep(0.3)
        reply = gdb.recv(8192)
        if b"m" not in reply[:2]:
            print(reply[:2000].decode("utf-8", "replace"))
            break
        body = reply.split(b"$", 1)[1].split(b"#", 1)[0][1:]
        print(body.decode("utf-8", "replace"))
        if reply.split(b"$", 1)[1][:1] == b"l":
            break
        offset += len(body)

    gdb.close()
    proc.kill()


main()
