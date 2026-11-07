"""C projects: gcc + ld + the project's own boot chain, composed into an image.

Layout comes from the manifest only. The boot chain (`stages`) is assembled to
raw binaries and dropped at sector boundaries from sector 1 on; the kernel is
linked at `kernel` and placed right behind the last stage. Nothing here decides
how many sectors the loader reads — that is the loader's own business now.
"""
import os
import re
import subprocess

from .. import config
from ..core.errors import AssembleError
from . import diskmap, disasm, linemap, workspace

SECTOR = 512
FLOPPY = 1474560
CFLAGS = ["-m32", "-ffreestanding", "-fno-pic", "-fno-stack-protector",
          "-fno-asynchronous-unwind-tables", "-fno-builtin", "-O0", "-g",
          "-Wall", "-Wextra", "-Wno-unused-parameter"]
DIAG = re.compile(r"^(?:.*[\\/])?([^\\/:]+):(\d+)(?::(\d+))?:\s*"
                  r"(?:fatal\s+)?(error|warning|note):\s*(.*)$")
SOURCE_DUMP = re.compile(r"^\s*(\d+\s*\||\|)")
BASE_TOKEN = "__KERNEL_BASE__"


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
    kernel_addr = plan["kernel"]
    includes = ["-I", workspace.root(base)]
    includes += ["-I", os.path.join(root, plan["dir"] or ".")]
    for item in plan["includes"]:
        includes += ["-I", os.path.join(root, plan["dir"] or ".", item)]

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
        if workspace.ext(source) in (".asm", ".s"):
            _run([config.NASM, "-f", "elf32", "-i", origin + os.sep, src, "-o", target])
        else:
            _run([tool("gcc"), *CFLAGS, *plan["cflags"], "-I", origin, *includes,
                  "-c", src, "-o", target], env)

    kernel = os.path.join(out_dir, "kernel.exe")
    script = _script(plan, out_dir, base)
    listing = ["-Map", os.path.join(out_dir, "map.txt")] if plan["map"] else []
    _run([tool("ld"), "-m", "i386pe", "--disable-reloc-section", "-T", script,
          "-e", plan["symbol"], *listing, *plan["ldflags"], *objects, "-o", kernel], env)

    # 同一份产物另存成 ELF：地址不变，但节与段的边界是写明的，能拿来看
    elf = os.path.join(out_dir, "kernel.elf")
    try:
        _run([tool("objcopy"), "-O", "elf32-i386", kernel, elf], env)
    except AssembleError:
        elf = ""

    flat = os.path.join(out_dir, "kernel.bin")
    _run([tool("objcopy"), "-O", "binary", "--strip-all", kernel, flat], env)

    stages = _stages(plan, out_dir, kernel_addr, flat, base)
    _compose(image, stages, flat, kernel_addr)
    return image, linemap.from_objects(config.OBJDUMP, kernel, plan,
                                       base=base, remap=remap)


def _script(plan, out_dir, base):
    """链接脚本原样用；带 __KERNEL_BASE__ 的替成清单里的地址。"""
    path = workspace.full(plan["link"], base)
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if BASE_TOKEN not in text:
        return path
    target = os.path.join(out_dir, "kernel.ld")
    with open(target, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text.replace(BASE_TOKEN, "0x%X" % plan["kernel"]))
    return target


def _stages(plan, out_dir, kernel_addr, flat, base):
    """汇编引导链，回报每级的字节和落点。"""
    if not plan["stages"]:
        raise AssembleError("%s 没写 stages，也没有 boot" % plan["entry"])
    sectors = ((os.path.getsize(flat) + SECTOR - 1) // SECTOR) if flat else 0
    defines = ["-D", "KERNEL_BASE=0x%X" % kernel_addr,
               "-D", "KERNEL_SEG=0x%X" % (kernel_addr >> 4),
               "-D", "KERNEL_SECTORS=%d" % sectors,
               "-D", "SECTORS=%d" % (sectors + len(plan["stages"]))]
    out = []
    for item in plan["stages"]:
        blob = os.path.join(out_dir, "stage%d.bin" % item["index"])
        source = workspace.full(item["path"], base)
        _run([config.NASM, "-f", "bin", "-i", os.path.dirname(source) + os.sep,
              *defines, source, "-o", blob])
        with open(blob, "rb") as fh:
            data = fh.read()
        if item["index"] == 0:
            if len(data) != SECTOR:
                raise AssembleError("引导扇区必须正好 512 字节，现在是 %d" % len(data))
            if data[510:512] != b"\x55\xaa":
                raise AssembleError("引导扇区结尾缺少 0xAA55")
        elif len(data) % SECTOR:
            raise AssembleError("stage %d（%s）%d 字节，不是整扇区，补到 %d"
                                % (item["index"], os.path.basename(item["path"]),
                                   len(data), ((len(data) // SECTOR) + 1) * SECTOR))
        out.append((blob, item["addr"], data))
    return out


def assemble_chain(plan, image, base=None):
    """纯汇编的自备引导链：只摆 stages，没有内核。"""
    out_dir = os.path.dirname(image)
    os.makedirs(out_dir, exist_ok=True)
    stages = _stages(plan, out_dir, plan["kernel"], None, base)
    _compose(image, stages, "", plan["kernel"])
    return image, {}


def _compose(image, stages, kernel, kernel_addr, chain_only=False):
    body = b""
    if kernel:
        with open(kernel, "rb") as fh:
            body = fh.read()
    data = bytearray()
    parts = []
    for index, (_blob, addr, blob) in enumerate(stages):
        start = len(data)
        data += blob
        parts.append((start, SECTOR if index == 0 else len(blob),
                      "boot" if index == 0 else "stage",
                      "引导扇区" if index == 0 else "引导第 %d 级" % index, addr))
    data += b"\x00" * ((-len(data)) % SECTOR)
    kernel_start = len(data)
    data += body
    if len(data) > FLOPPY:
        raise AssembleError("镜像 %d 字节，超过软盘容量 %d（内核 %d 字节，起点第 %d 扇区）"
                            % (len(data), FLOPPY, len(body), kernel_start // SECTOR + 1))
    parts.append((kernel_start, len(body), "code",
                  "内核负载（链接在 0x%X，第 %d 扇区起）"
                  % (kernel_addr, kernel_start // SECTOR + 1), kernel_addr))
    diskmap.record(image, parts)
    data += b"\x00" * (FLOPPY - len(data))
    with open(image, "wb") as fh:
        fh.write(data)
    regions = [(blob, addr, 16) for blob, addr, _data in stages if addr]
    disasm.build_split(image, regions + [(kernel, kernel_addr, 32)])


def run_command(plan, image, base=None):
    """`build = [...]`：整条流水线交给项目自己的命令，只收产物。"""
    directory = workspace.root(base)
    cwd = os.path.join(directory, plan["dir"]) if plan["dir"] else directory
    if not os.path.isdir(cwd):
        raise AssembleError("工程目录不见了：%s" % plan["dir"])
    line = plan["build"][0] if len(plan["build"]) == 1 else plan["build"]
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([os.path.dirname(config.NASM),
                                   os.path.dirname(config.C_OBJCOPY),
                                   env.get("PATH", "")])
    result = subprocess.run(line, shell=isinstance(line, str), cwd=cwd,
                            capture_output=True, text=True, env=env)
    if result.returncode != 0:
        message = _clean(result.stderr) or _clean(result.stdout)
        raise AssembleError(message or "构建命令失败（退出码 %d）" % result.returncode)
    made = workspace.full(plan["image"], base)
    if not os.path.isfile(made):
        raise AssembleError("构建命令跑完了，但没有产出 %s" % plan["image"])
    with open(made, "rb") as fh:
        data = fh.read()
    if len(data) < SECTOR or len(data) % SECTOR:
        raise AssembleError("产物 %d 字节，不是整扇区" % len(data))
    if data[510:512] != b"\x55\xaa":
        raise AssembleError("产物的第一个扇区结尾缺少 0xAA55")
    if len(data) > FLOPPY:
        raise AssembleError("产物 %d 字节，超过软盘容量 %d" % (len(data), FLOPPY))
    os.makedirs(os.path.dirname(image), exist_ok=True)
    with open(image, "wb") as fh:
        fh.write(data)
    diskmap.record(image, [(0, len(data), "code", "整盘（项目自己铺的）", plan["base"])])
    head = os.path.join(os.path.dirname(image), "head.bin")
    with open(head, "wb") as fh:
        fh.write(data[:SECTOR])
    disasm.build_split(image, [(head, plan["base"], 16)])
    table = {}
    elf = plan["elf"] and workspace.full(plan["elf"], base)
    if elf and os.path.isfile(elf):
        try:
            table = linemap.from_objects(config.OBJDUMP, elf, plan, base=base)
        except Exception:            # 行号是加分项，别让它挡住构建
            table = {}
    return image, table


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
