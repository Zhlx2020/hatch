"""Can ^C on the pipe break a running Bochs into the debugger?"""
import os
import socket
import subprocess
import threading
import time

BOCHS = r"C:\software\Bochs-3.0\bochs.exe"
SHARE = r"C:\software\Bochs-3.0"
D = os.path.dirname(os.path.abspath(__file__))
BOOT = bytes.fromhex("ebfe") * 256


def main():
    work = os.path.join(D, "probe_break")
    os.makedirs(work, exist_ok=True)
    img = os.path.join(work, "b.img")
    data = bytearray(BOOT)
    data[510:512] = b"\x55\xaa"
    with open(img, "wb") as fh:
        fh.write(bytes(data))
    cfg = os.path.join(work, "b.bochsrc")
    with open(cfg, "w", newline="\n") as fh:
        fh.write(
            'romimage: file="%s/BIOS-bochs-latest"\n'
            'vgaromimage: file="%s/VGABIOS-elpin-2.40"\n'
            "megs: 32\n"
            'floppya: 1_44="%s", status=inserted\n'
            "boot: a\n"
            'display_library: rfb, options="timeout=300, no_gui_console"\n'
            % (SHARE, SHARE, img)
        )
    proc = subprocess.Popen([BOCHS, "-q", "-f", cfg, "-debugger"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    threading.Thread(target=lambda: [out.append(x.rstrip()) for x in proc.stdout],
                     daemon=True).start()
    time.sleep(1.2)
    proc.stdin.write("c\n")
    proc.stdin.flush()
    sock = socket.create_connection(("127.0.0.1", 5900), 5)
    sock.settimeout(5)
    sock.recv(12)
    sock.send(b"RFB 003.003\n")
    sock.recv(4)
    sock.send(b"\x01")
    sock.recv(64)
    time.sleep(1.5)
    print("running, lines:", len(out), "last:", out[-1][:60] if out else "")

    proc.stdin.write("\x03")
    proc.stdin.flush()
    time.sleep(1.0)
    print("after ^C, prompt back:", any("<bochs:" in x for x in out[-3:]))
    print("tail:", [x[:60] for x in out[-3:]])

    proc.stdin.write("r\n")
    proc.stdin.flush()
    time.sleep(1.0)
    print("after r, tail:", [x[:60] for x in out[-4:]])

    sock.close()
    time.sleep(0.3)
    proc.kill()


main()
