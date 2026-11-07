"""Read an ELF file and report its real structure.

The C toolchain here targets PE, so the build converts the linked image to
ELF32 with objcopy: same code, same addresses, but section/segment boundaries
are stated instead of implied. binutils stays the reference for symbols — this
module only parses what it must and cross-checks with objdump.
"""
import os
import struct
import subprocess

from .. import config
from ..core.errors import AssembleError

TYPES = {0: "无", 1: "可装入程序段", 2: "符号表", 3: "字符串表", 4: "重定位",
         8: "无内容（.bss）", 9: "重定位", 1_0: ""}
NAMES = {1: "PROGBITS", 2: "SYMTAB", 3: "STRTAB", 4: "RELA", 8: "NOBITS",
         9: "REL", 14: "INIT_ARRAY", 15: "FINI_ARRAY", 17: "NOTE", 23: "INIT",
         24: "FINI", "other": "其它"}
MACHINE = {3: "i386", 62: "x86-64", 40: "ARM"}
KIND = {"l": "局部", "g": "全局", "w": "弱", "u": "未定义", "a": "绝对"}
HEADER_TYPE = {1: "可重定位文件（.o）", 2: "可执行文件", 3: "共享库", 4: "核心转储"}
FLAG_LETTER = {0x1: "W", 0x2: "A", 0x4: "X"}
SHF_WRITE, SHF_ALLOC, SHF_EXEC = 0x1, 0x2, 0x4


def _flags(value):
    letters = "".join(letter for bit, letter in FLAG_LETTER.items() if value & bit)
    return letters or "-"


def _read(path):
    with open(path, "rb") as fh:
        return fh.read()


def _parse(data, warnings):
    if data[:4] != b"\x7fELF":
        return {"format": "unknown"}
    bits = data[4]
    endian = "<" if data[5] == 1 else ">"
    if bits != 1:
        warnings.append("这是 ELF%d，这里按 32 位解析会不准" % (32 if bits == 1 else 64))
    (kind, machine, version, entry, phoff, shoff, flags, ehsize, phentsize,
     phnum, shentsize, shnum, shstrndx) = struct.unpack(endian + "HHIIIIIHHHHHH", data[16:52])
    head = {
        "format": "elf", "bits": bits * 32, "endian": "小端" if endian == "<" else "大端",
        "type": HEADER_TYPE.get(kind, str(kind)), "machine": MACHINE.get(machine, str(machine)),
        "version": version, "entry": entry, "flags": flags,
        "ehsize": ehsize, "phentsize": phentsize, "phnum": phnum,
        "shentsize": shentsize, "shnum": shnum, "shstrndx": shstrndx,
    }
    sections = []
    for index in range(shnum):
        at = shoff + index * shentsize
        if at + 40 > len(data):
            warnings.append("节表第 %d 项越过文件末尾" % index)
            break
        (name, stype, sflags, addr, offset, size, link, info, align, entsize) = \
            struct.unpack(endian + "IIIIIIIIII", data[at:at + 40])
        sections.append({"index": index, "name_off": name, "type_id": stype,
                         "type": NAMES.get(stype, NAMES["other"]), "flags": _flags(sflags),
                         "addr": addr, "offset": offset, "size": size, "link": link,
                         "info": info, "align": align, "entsize": entsize,
                         "name": ""})
    names = b""
    if 0 <= shstrndx < len(sections):
        table = sections[shstrndx]
        names = data[table["offset"]:table["offset"] + table["size"]]
    for section in sections:
        chunk = names[section["name_off"]:].split(b"\x00", 1)
        section["name"] = chunk[0].decode("latin-1") if chunk else ""
        if section["type_id"] in (8, 2, 3):
            section["raw"] = ""
        else:
            section["raw"] = data[section["offset"]:section["offset"] + 12].hex(" ")
        if section["offset"] + section["size"] > len(data) and section["type_id"] != 8:
            warnings.append("节 %s 的内容超出文件末尾" % (section["name"] or section["index"]))
    segments = []
    for index in range(phnum):
        at = phoff + index * phentsize
        if at + 32 > len(data):
            warnings.append("程序头第 %d 项越过文件末尾" % index)
            break
        (ptype, offset, vaddr, paddr, filesz, memsz, pflags, align) = \
            struct.unpack(endian + "IIIIIIII", data[at:at + 32])
        segments.append({"index": index, "type": ptype, "offset": offset,
                         "vaddr": vaddr, "paddr": paddr, "filesz": filesz,
                         "memsz": memsz, "flags": "" if not pflags else "RWX"[0:0]
                         + ("R" if pflags & 4 else "-") + ("W" if pflags & 2 else "-")
                         + ("X" if pflags & 1 else "-"), "align": align})
        if filesz > memsz:
            warnings.append("段 %d 的文件长度大于内存长度" % index)
        if memsz > filesz and not (memsz - filesz):
            warnings.append("段 %d 需要清零 %d 字节" % (index, memsz - filesz))
    return {**head, "sections": sections, "segments": segments}


def _symbols(path):
    """符号交给 objdump，它是 binutils 自己的解释。"""
    found = config.__dict__.get("OBJDUMP") or ""
    if not found or not os.path.exists(found):
        return [], ["没有 objdump，符号表略过"]
    try:
        result = subprocess.run([found, "-t", "-W", path], capture_output=True, text=True)
    except OSError as exc:
        return [], ["objdump 起不来：%s" % exc]
    rows, warnings = [], []
    for line in (result.stdout or "").splitlines():
        parts = line.split()
        if len(parts) < 4 or not parts[0].rstrip(":").isdigit():
            continue
        try:
            value = int(parts[0].rstrip(":"), 16)
        except ValueError:
            continue
        # objdump -t 的列：地址 作用域 类型 节 大小 名字
        if len(parts) < 6:
            continue
        rows.append({"value": "0x%08x" % value, "size": parts[4],
                     "kind": KIND.get(parts[1], parts[1]),
                     "section": parts[3], "name": " ".join(parts[5:])})
    if not rows:
        warnings.append("objdump 没给出符号（可能已被 strip）")
    return rows, warnings


def _checks(head, warnings):
    if head.get("format") != "elf":
        warnings.append("文件开头不是 ELF 魔数")
        return
    if not head["sections"] and not head["segments"]:
        warnings.append("既没有节表也没有程序头，只剩文件头")
    entry = head["entry"]
    texts = [s for s in head["sections"] if s["flags"].find("X") >= 0 and s["size"]]
    if entry and texts and not any(s["addr"] <= entry < s["addr"] + s["size"] for s in texts):
        warnings.append("入口 0x%08x 不在任何可执行节里" % entry)
    for section in head["sections"]:
        if "W" in section["flags"] and "X" in section["flags"]:
            warnings.append("节 %s 既可写又可执行" % section["name"])
        if section["align"] > 0x10000:
            warnings.append("节 %s 对齐 %d 字节，偏大" % (section["name"], section["align"]))


def describe(path):
    if not os.path.isfile(path):
        raise AssembleError("没有 ELF 产物：%s" % os.path.basename(path))
    data = _read(path)
    warnings = []
    head = _parse(data, warnings)
    head["size"] = len(data)
    head["path"] = os.path.basename(path)
    if head.get("format") == "elf":
        _checks(head, warnings)
        symbols, notes = _symbols(path)
        head["symbols"] = symbols[:200]
        head["symbol_total"] = len(symbols)
        warnings += notes
        head["allocated"] = sum(s["size"] for s in head["sections"] if "A" in s["flags"])
        head["file_bytes"] = sum(s["size"] for s in head["sections"]
                                 if s["type_id"] != 8)
    head["warnings"] = warnings
    return head
