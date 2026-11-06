"""Bochs process: session dir, bochsrc, spawn, lifecycle."""
import os
import subprocess

from ... import config
from .protocol import Protocol

CONFIG_TEMPLATE = """romimage: file="{share}/BIOS-bochs-latest"
vgaromimage: file="{share}/VGABIOS-elpin-2.40"
megs: 32
floppya: 1_44="{image}", status=inserted
boot: a
log: "{log}"
display_library: rfb, options="timeout={timeout}, no_gui_console"
magic_break: enabled=1
"""


def make_session_dir():
    os.makedirs(config.RUN_DIR, exist_ok=True)
    n = 1
    while os.path.exists(os.path.join(config.RUN_DIR, "s%02d" % n)):
        n += 1
    path = os.path.join(config.RUN_DIR, "s%02d" % n)
    os.makedirs(path)
    return path


class BochsProcess:
    def __init__(self, session_dir, image):
        self.dir = session_dir
        self.image = image
        self.proc = None
        self.protocol = None

    def start(self):
        cfg = os.path.join(self.dir, "sandbox.bochsrc")
        with open(cfg, "w", newline="\n") as fh:
            fh.write(CONFIG_TEMPLATE.format(
                share=config.BOCHS_SHARE,
                image=self.image,
                log=os.path.join(self.dir, "bochs.log"),
                timeout=config.BOOT_TIMEOUT,
            ))
        self.proc = subprocess.Popen(
            [config.BOCHS, "-q", "-f", cfg, "-debugger"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        self.protocol = Protocol(self.proc)

    @property
    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def stop(self):
        if self.alive:
            self.protocol.shutdown()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
