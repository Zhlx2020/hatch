"""Does debugger output reach stdout when the rfb GUI console is disabled?"""
import os
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time

BOCHS = r"C:\software\Bochs-3.0\bochs.exe"
SHARE = r"C:\software\Bochs-3.0"
D = os.path.dirname(os.path.abspath(__file__))


def main(option):
    work = os.path.join(D, "probe_nogui")
    os.makedirs(work, exist_ok=True)
    img = os.path.join(work, "b.img")
    with open(img, "wb") as fh:
        fh.write(b"\xf4" * 512)
    cfg = os.path.join(work, "b.bochsrc")
    with open(cfg, "w", newline="\n") as fh:
        fh.write(
            'romimage: file="%s/BIOS-bochs-latest"\n'
            'vgaromimage: file="%s/VGABIOS-elpin-2.40"\n'
            "megs: 32\n"
            'floppya: 1_44="%s", status=inserted\n'
            "boot: a\n"
            'display_library: rfb, options="timeout=300%s"\n'
            % (SHARE, SHARE, img, option)
        )
    proc = subprocess.Popen([BOCHS, "-q", "-f", cfg, "-debugger"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []

    def pump():
        for line in proc.stdout:
            out.append(line.rstrip())

    threading.Thread(target=pump, daemon=True).start()
    time.sleep(1.5)
    print('OUT', out[-6:])

    s = socket.create_connection(("127.0.0.1", 5900), 3)
    s.recv(12)
    s.send(b"RFB 003.003\n")
    s.recv(4)
    s.send(b"\x01")
    head = s.recv(1024)
    print("serverinit bytes", len(head))
    time.sleep(0.8)

    proc.stdin.write("r\n")
    proc.stdin.flush()
    time.sleep(1.5)
    print("---- stdout ----")
    for line in out[-25:]:
        print(repr(line[:100]))
    proc.stdin.write("q\n")
    proc.stdin.flush()
    try:
        proc.wait(3)
    except subprocess.TimeoutExpired:
        proc.kill()
    s.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ", no_gui_console")

