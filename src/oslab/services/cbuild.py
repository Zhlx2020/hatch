"""Compile a C project from its manifest into a bootable flat image.

W64devkit's binutils only target PE, so the recipe is: compile to PE objects,
link them with a script pinned at the kernel base, pull `.text/.rodata/.data`
out with objcopy, prepend the 16-bit boot stub and pad into a floppy image.
The same objects are also linked as a debug image, which is what produces the
line map used by editor breakpoints.
"""
import os
import re
import subprocess

from .. import config
from ..core.errors import AssembleError
from . import diskmap, disasm, linemap, workspace

SECTOR = 512
FLOPPY = 1474560
LOAD_SECTORS = 32                     # 与 boot.asm 的 SECTORS 保持一致
KERNEL_LIMIT = (LOAD_SECTORS - 1) * SECTOR
KERNEL_BASE = 0x10000
CFLAGS = ["-m32", "-ffreestanding", "-fno-pic", "-fno-stack-protector",
          "-fno-asynchronous-unwind-tables", "-fno-builtin", "-O0", "-g",
          "-Wall", "-Wextra", "-Wno-unused-parameter"]
DIAG = re.compile(r"^(?:.*[\\/])?([^\\/:]+):(\d+)(?::(\d+))?:\s*"
                   r"(?:fatal\s+)?(error|warning|note):\s*(.*)$")
SOURCE_DUMP = re.compile(r"^\s*(\d+\s*\||\|)")


def tool(name):
    found = config.__dict__.get("C_" + name.upper())
    if found and os.path.exists(found):
        return found
    raise AssembleError("找不到 %s，检查工装目录" % name)


def compile_project(plan, image, base=None, text=None):
    """`text` replaces the entry source when it is the file being run."""
    root = workspace.root(base)
    out_dir = os.path.dirname(image)
    os.makedirs(out_dir, exist_ok=True)
    env = {k: v for k, v in os.environ.items()
           if k.upper() not in ("TMP", "TEMP", "TMPDIR")}
    env.update(TMP=out_dir, TEMP=out_dir, TMPDIR=out_dir)

    objects = []
    remap = {}
    for index, source in enumerate(plan["sources"]):
        target = os.path.join(out_dir, "u%d.o" % index)
        objects.append(target)
        if text is not None and source == plan["entry"]:
            stage_dir = os.path.join(out_dir, "u%d" % index)
            os.makedirs(stage_dir, exist_ok=True)
            staged = os.path.join(stage_dir, os.path.basename(source))
            with open(staged, "w", newline="\n", encoding="utf-8") as fh:
                fh.write(text)
            src = staged
            remap[staged] = source
        else:
            src = workspace.full(source, base)
        origin = os.path.dirname(workspace.full(source, base))
        _run([tool("gcc"), *CFLAGS, "-I", origin, "-I", os.path.join(root, plan["dir"] or "."),
              "-c", src, "-o", target], env)

    kernel = os.path.join(out_dir, "kernel.exe")
    _run([tool("ld"), "-m", "i386pe", "--disable-reloc-section", "-T",
          workspace.full(plan["link"], base), "-e", "_start", *objects, "-o", kernel], env)

    flat = os.path.join(out_dir, "kernel.bin")
    _run([tool("objcopy"), "-O", "binary", "--strip-debug",
          "-j", ".text", "-j", ".rdata", "-j", ".rodata", "-j", ".data",
          kernel, flat], env)

    # 同一份产物另存成 ELF：地址不变，但节与段的边界是写明的，能拿来看
    elf = os.path.join(out_dir, "kernel.elf")
    try:
        _run([tool("objcopy"), "-O", "elf32-i386", kernel, elf], env)
    except AssembleError:
        elf = ""

    stub = os.path.join(out_dir, "stub.bin")
    _run([config.NASM, "-f", "bin", workspace.full(plan["boot"], base), "-o", stub])

    diskmap.record(image, [(0, SECTOR, "boot", "引导扇区 %s（载入 0x%x）"
                            % (os.path.basename(plan["boot"]), plan["base"]), plan["base"]),
                           (SECTOR, os.path.getsize(flat), "code",
                            "内核负载（从 0x%x 起）" % KERNEL_BASE, KERNEL_BASE)])
    _compose(image, stub, flat)
    disasm.build_split(image, [(stub, plan["base"], 16), (flat, KERNEL_BASE, 32)])
    return image, linemap.from_objects(config.OBJDUMP, kernel, plan,
                                       base=base, remap=remap)


def _run(args, env=None):
    result = subprocess.run(args, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        message = _clean(result.stderr) or _clean(result.stdout)
        raise AssembleError(message or "%s 失败" % os.path.basename(args[0]))


def _clean(output):
    """Keep `file:line: kind: message`, drop paths and echoed source lines."""
    lines = []
    for raw in (output or "").strip().splitlines():
        line = raw.strip()
        match = DIAG.match(line)
        if match:
            lines.append("%s:%s: %s: %s" % (match.group(1), match.group(2),
                                            match.group(4), match.group(5)))
        elif SOURCE_DUMP.match(line) or line.startswith("In function"):
            continue
        elif line.startswith("^"):
            continue
        elif line:
            lines.append(line)
    return "\n".join(lines)


def _compose(image, stub, kernel):
    with open(stub, "rb") as fh:
        head = fh.read()
    with open(kernel, "rb") as fh:
        body = fh.read()
    if len(head) != SECTOR:
        raise AssembleError("引导扇区必须正好 512 字节，现在是 %d" % len(head))
    if head[510:512] != b"\x55\xaa":
        raise AssembleError("引导扇区结尾缺少 0xAA55")
    if len(body) > KERNEL_LIMIT:
        raise AssembleError("内核 %d 字节，引导扇区只能载入 %d" % (len(body), KERNEL_LIMIT))
    data = bytearray(head) + body
    if len(data) > FLOPPY:
        raise AssembleError("镜像 %d 字节，超过软盘容量" % len(data))
    data += b"\x00" * (FLOPPY - len(data))
    with open(image, "wb") as fh:
        fh.write(data)
