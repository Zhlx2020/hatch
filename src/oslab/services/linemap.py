"""Line to address maps, so the gutter can drop a breakpoint on a source line.

Two producers feed this: the nasm listing for assembly and `objdump -dl` for C.
Both yield `{path: {line: addr}}`; the first address of a line wins, because a
breakpoint on a source line means "stop where this line starts".
"""
import os
import re

from . import sourcemap, workspace

DWARF = re.compile(r"^(.*):(\d+)$")
ADDRESS = re.compile(r"^\s*([0-9a-f]+):\s")
LISTING = re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]{8})\s")


def _rel(path, root):
    clean = os.path.abspath(path).replace("\\", "/")
    root = os.path.abspath(root).replace("\\", "/").rstrip("/") + "/"
    if clean.lower().startswith(root.lower()):
        return clean[len(root):]
    return clean


def from_objects(objdump, image, plan, base=None, remap=None):
    """Parse `objdump -dl` for the debug image of a C project."""
    import subprocess

    result = subprocess.run([objdump, "-dl", image], capture_output=True, text=True)
    table = {}
    current = None
    root = workspace.root(base)
    remap = {os.path.abspath(k).replace("\\", "/"): v for k, v in (remap or {}).items()}
    for raw in result.stdout.splitlines():
        match = DWARF.match(raw.strip())
        if match and not ADDRESS.match(raw):
            current = (match.group(1), int(match.group(2)))
            continue
        address = ADDRESS.match(raw)
        if not address or current is None:
            continue
        name, line = current
        rel = remap.get(os.path.abspath(name).replace("\\", "/")) or _rel(name, root)
        table.setdefault(rel, {})
        table[rel].setdefault(line, int(address.group(1), 16))
    return table


def from_listing(image, path):
    """Reverse the nasm listing that the assembler already wrote."""
    table = {}
    straight = sourcemap.load(image)
    for addr, line in straight.items():
        table.setdefault(path, {}).setdefault(line, addr)
    return table


def lookup(table, path, line):
    lines = table.get(workspace.safe(path)) or {}
    if not lines:
        return 0
    if line in lines:
        return lines[line]
    for probe in range(1, 6):
        if line + probe in lines:
            return lines[line + probe]
    return 0
