"""Map machine addresses back to source lines using the nasm listing."""
import os
import re

LINE = re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]{8})\s")
BASE = 0x7C00


def load(image):
    path = image + ".lst"
    table = {}
    if not os.path.exists(path):
        return table
    with open(path, encoding="utf-8", errors="replace") as fh:
        pairs = [
            (int(match.group(2), 16), int(match.group(1)))
            for match in (LINE.match(raw) for raw in fh)
            if match
        ]
    if not pairs:
        return table
    # nasm prints section offsets when the code starts at ORG 0x7C00
    offset_form = max(addr for addr, _ in pairs) < BASE
    for addr, line in pairs:
        table[addr + BASE if offset_form else addr] = line
    return table


def line_at(table, addr):
    if not table:
        return 0
    for probe in range(0, 16):
        found = table.get(addr - probe)
        if found:
            return found
    return 0
