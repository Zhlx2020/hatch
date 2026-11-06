"""Which console mode lets CTRL_C interrupt Bochs into the debugger?"""
import ctypes
import os
import socket
import subprocess
import sys
import threading
import time

BOCHS = r"C:\software\Bochs-3.0\bochs.exe"
SHARE = r"C:\software\Bochs-3.0"
D = os.path.dirname(os.path.abspath(__file__))
FLAGS = {
    "newcon": subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP,
    "nowin": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
}
CTRL_C = 0


def main(mode):
    work = os.path.join(D, "probe_ctrlc_mode")
    os.makedirs(work, exist_ok=True)
    img = os.path.join(work, "b.img")
    data = bytearray(b"\xeb\xfe" * 256)
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
                            stderr=subprocess.STDOUT, text=True, bufsize=1,
                            creationflags=FLAGS[mode])
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
    sock.recv(256)
    time.sleep(1.5)

    print(mode, "alive:", proc.poll() is None)
    print("ctrl-c sent:", ctypes.windll.kernel32.GenerateConsoleCtrlEvent(CTRL_C, proc.pid))
    time.sleep(1.2)
    print("alive after:", proc.poll() is None)
    print("prompt back:", any("<bochs:" in x for x in out[-4:]))
    print("tail:", [x[:60] for x in out[-3:]])
    if proc.poll() is None:
        try:
            proc.stdin.write("r\n")
            proc.stdin.flush()
            time.sleep(1.2)
            print("after r:", [x[:70] for x in out[-4:]])
        except OSError as exc:
            print("write failed:", exc)
    sock.close()
    time.sleep(0.2)
    if proc.poll() is None:
        proc.kill()


main(sys.argv[1] if len(sys.argv) > 1 else "newcon")
