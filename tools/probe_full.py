"""Full rfb handshake, then drive the debugger over the pipe."""
import os
import socket
import subprocess
import threading
import time

BOCHS = r"C:\software\Bochs-3.0\bochs.exe"
SHARE = r"C:\software\Bochs-3.0"
D = os.path.dirname(os.path.abspath(__file__))


def main():
    work = os.path.join(D, "probe_full")
    os.makedirs(work, exist_ok=True)
    img = os.path.join(work, "b.img")
    with open(img, "wb") as fh:
        fh.write(b"\xeb\xfe" * 256)
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
    print("banner:", sock.recv(12))
    sock.send(b"RFB 003.003\n")
    print("sectype:", sock.recv(4))
    sock.send(b"\x01")
    head = sock.recv(64)
    print("serverinit:", len(head))
    time.sleep(1.0)

    for command in ("r", "xp /4xb 0x7c00"):
        proc.stdin.write(command + "\n")
        proc.stdin.flush()
        time.sleep(1.2)
        print("after", command, "->", [x[:50] for x in out[-4:]])

    print("total lines:", len(out))
    proc.stdin.write("q\n")
    proc.stdin.flush()
    time.sleep(0.8)
    proc.kill()
    sock.close()


main()
