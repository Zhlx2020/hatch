"""Assemble a flat binary from editor text.

Boot sectors are exactly 512 bytes with a 0xAA55 tail; anything larger is padded
into a 1.44 MB floppy image so multi-sector experiments still boot.
"""
import os
import re
import subprocess

from .. import config
from ..core.errors import AssembleError
from . import disasm

SECTOR = 512
FLOPPY = 1474560
DISASM_BYTES = re.compile(r"^\s*[0-9a-f]{4,16}:\s+((?:[0-9a-f]{2}\s)+)")
NASM_LINE = re.compile(r"^(?:.*[\\/])?([^\\/]+\.asm):(\d+):\s*(?:error|warning)?:?\s*(.*)$")


def assemble(source, out_path, includes=()):
    asm = out_path + ".asm"
    with open(asm, "w", newline="\n", encoding="ascii", errors="replace") as fh:
        fh.write(source)
    args = [config.NASM, "-f", "bin", asm, "-o", out_path]
    for directory in includes:
        args[1:1] = ["-i", directory + os.sep]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssembleError(_clean(result.stderr) or "汇编失败")
    size = os.path.getsize(out_path)
    if size > FLOPPY:
        raise AssembleError("产物 %d 字节，超过软盘容量" % size)
    with open(out_path, "rb") as fh:
        data = fh.read()
    if size == SECTOR and data[510:512] != b"\x55\xaa":
        raise AssembleError("引导扇区结尾缺少 0xAA55")
    if size < SECTOR:
        raise AssembleError("产物只有 %d 字节，不足 512" % size)
    if size % SECTOR:
        data += b"\x00" * (SECTOR - size % SECTOR)
    data += b"\x00" * (FLOPPY - len(data))
    with open(out_path, "wb") as fh:
        fh.write(data)
    disasm.build(out_path)
    return out_path


def _clean(stderr):
    """Show only file:line: message, never the full session path."""
    lines = []
    for line in stderr.strip().splitlines():
        match = NASM_LINE.match(line.strip())
        lines.append("%s:%s %s" % (match.group(1), match.group(2), match.group(3))
                     if match else line.strip())
    return "\n".join(lines)
