"""Does the guest's COM1 output reach QEMU's serial chardev?"""
import os
import socket
import subprocess
import time

QEMU = r"C:\Program Files\qemu\qemu-system-i386.exe"
D = os.path.dirname(os.path.abspath(__file__))
import glob
IMG = max(glob.glob(os.path.join(D, "..", ".run", "q*", "boot.img")), key=os.path.getmtime)


def main():
    print("image:", IMG, os.path.exists(IMG))
    listener = socket.create_server(("127.0.0.1", 5915))
    proc = subprocess.Popen(
        [QEMU, "-drive", "file=%s,if=floppy,format=raw" % IMG, "-boot", "a",
         "-m", "32", "-display", "none", "-monitor", "none",
         "-serial", "tcp:127.0.0.1:5915"],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    conn, _ = listener.accept()
    conn.settimeout(6)
    data = b""
    start = time.time()
    try:
        while time.time() - start < 6:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"HELLO" in data:
                break
    except socket.timeout:
        pass
    print("serial bytes:", data[:120])
    conn.close()
    listener.close()
    proc.kill()


main()
