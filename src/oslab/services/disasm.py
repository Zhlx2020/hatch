"""Static disassembly of the built flat binary, served by address.

The QEMU gdb stub has no disassembler, so we build one pass with objdump at
assemble time and answer lookups from that map instead of guessing.
"""
import os
import re
import subprocess

from .. import config

LINE = re.compile(r"^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(.*)$")


def build(image, base=0x7C00, out=None):
    out = out or image + ".dis"
    result = subprocess.run(
        [config.OBJDUMP, "-D", "-b", "binary", "-m", "i386",
         "--adjust-vma=0x%x" % base, image],
        capture_output=True, text=True,
    )
    lines = []
    for line in result.stdout.splitlines():
        match = LINE.match(line)
        if match:
            lines.append("%08x: %-24s %s" % (int(match.group(1), 16),
                                             match.group(2).strip(), match.group(3)))
    with open(out, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return out


def load(image):
    path = image + ".dis"
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def around(lines, addr, count=8):
    if not lines:
        return ""
    for index, line in enumerate(lines):
        if int(line[:8], 16) >= addr:
            return "\n".join(lines[index:index + count])
    return "\n".join(lines[-count:])


def rows(lines, addr, count=16):
    if not lines:
        return []
    start = 0
    for index, line in enumerate(lines):
        if int(line[:8], 16) >= addr:
            start = index
            break
    else:
        start = max(0, len(lines) - count)
    out = []
    for line in lines[start:start + count]:
        address, rest = line.split(":", 1)
        text = rest.strip()
        if "  " in text:
            bytes_, mnemonic = text.split("  ", 1)
        else:
            bytes_, mnemonic = "", text
        out.append({"addr": address, "bytes": bytes_.strip(),
                    "text": mnemonic.strip()})
    return out

