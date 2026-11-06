"""Static disassembly of the built flat binary, served by address.

The QEMU gdb stub has no disassembler, so we build the map with objdump at
assemble time and answer lookups from it instead of guessing. Both syntaxes are
written; Intel is the default.
"""
import os
import re
import subprocess

from .. import config

LINE = re.compile(r"^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(.*)$")
SYNTAXES = ("intel", "att")
DEFAULT = "intel"


def path(image, syntax=DEFAULT):
    return "%s.dis.%s" % (image, syntax if syntax in SYNTAXES else DEFAULT)


def build(image, base=0x7C00, out=None):
    written = []
    for syntax in SYNTAXES:
        target = out if (out and len(SYNTAXES) == 1) else path(image, syntax)
        result = subprocess.run(
            [config.OBJDUMP, "-D", "-b", "binary", "-m", "i386", "-M", "i8086,%s" % syntax,
             "--insn-width=16", "--adjust-vma=0x%x" % base, image],
            capture_output=True, text=True,
        )
        lines = []
        for line in result.stdout.splitlines():
            match = LINE.match(line)
            if match:
                lines.append("%08x: %-24s %s" % (int(match.group(1), 16),
                                                 match.group(2).strip(), match.group(3)))
        with open(target, "w", newline="\n", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        written.append(target)
    return written[0]


def build_split(image, regions, out=None):
    """Disassemble several (file, address, bits) regions into one sorted map.

    A boot stub and a kernel linked far apart cannot share one linear pass: the
    stub is 16-bit at 0x7C00 and the kernel is 32-bit at 0x10000, so each region
    gets its own base and decoder and the results are merged by address.
    """
    written = []
    for syntax in SYNTAXES:
        lines = []
        for source, base, bits in regions:
            arch = "i8086" if bits == 16 else "i386"
            result = subprocess.run(
                [config.OBJDUMP, "-D", "-b", "binary", "-m", "i386",
                 "-M", "%s,%s" % (arch, syntax), "--insn-width=16",
                 "--adjust-vma=0x%x" % base, source],
                capture_output=True, text=True,
            )
            for line in result.stdout.splitlines():
                match = LINE.match(line)
                if match:
                    lines.append((int(match.group(1), 16), match.group(2).strip(),
                                  match.group(3)))
        lines.sort(key=lambda row: row[0])
        target = out or path(image, syntax)
        with open(target, "w", newline="\n", encoding="utf-8") as fh:
            fh.write("\n".join("%08x: %-24s %s" % row for row in lines))
        written.append(target)
    return written[0]


def load(image, syntax=DEFAULT):
    name = path(image, syntax)
    if not os.path.exists(name):
        other = path(image, "att" if syntax == DEFAULT else DEFAULT)
        if not os.path.exists(other):
            return []
        name = other
    with open(name, encoding="utf-8") as fh:
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
