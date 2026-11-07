"""Build a flat binary out of a project manifest (`oslab.toml`).

The manifest is the only source of truth: kind, entry, sources and the link
script all come from the file next to the project, never from a guess about the
suffix. Constraints are checked here so a broken manifest fails loudly instead
of building something that quietly does not boot.
"""
import os
import tomllib

from ..core.errors import OsLabError
from . import workspace

MANIFEST = "oslab.toml"
KINDS = ("asm", "c")
DEFAULT_BASE = 0x7C00
DEFAULT_KERNEL = 0x10000
DEFAULT_SYMBOL = "_start"
KERNEL_MAX = 0x100000
KEYS = ("kind", "entry", "sources", "boot", "stages", "link", "kernel", "base",
        "symbol", "cflags", "ldflags", "includes", "build", "image", "elf", "map", "qemu")
QEMU_KEYS = ("profile", "memory", "disks", "extra")
C_ONLY = ("sources", "link", "kernel", "symbol", "cflags",
          "ldflags", "includes")
ASM_OK = (".asm", ".s")
RUNNABLE = (".asm", ".c", ".s")


def find(path, base=None):
    """Nearest ancestor directory of `path` that carries a manifest."""
    root = workspace.root(base)
    try:
        current = os.path.dirname(workspace.full(path, base))
    except OsLabError:
        return ""
    while current.startswith(root):
        if os.path.isfile(os.path.join(current, MANIFEST)):
            return os.path.relpath(current, root).replace(os.sep, "/")
        if os.path.abspath(current) == os.path.abspath(root):
            break
        current = os.path.dirname(current)
    return ""


def _join(directory, name):
    return (directory + "/" + name) if directory else name


def _number(raw, key, default, low, high, align=1):
    value = raw.get(key, default)
    try:
        number = value if isinstance(value, int) else int(str(value), 0)
    except ValueError as exc:
        raise OsLabError("%s：%s 要是个地址，比如 0x%X" % (MANIFEST, key, default)) from exc
    if not low <= number <= high:
        raise OsLabError("%s：%s 得在 0x%X 到 0x%X 之间（现在是 0x%X）"
                         % (MANIFEST, key, low, high, number))
    if number % align:
        raise OsLabError("%s：%s 要 %d 字节对齐（现在是 0x%X）"
                         % (MANIFEST, key, align, number))
    return number


def _list(raw, key):
    value = raw.get(key)
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip()
                                              for item in value):
        raise OsLabError("%s：%s 要是个字符串列表" % (MANIFEST, key))
    return [item.strip() for item in value]


def _stages(raw, rel):
    """`stages` / `boot` → 依次落盘的引导链，第一个是引导扇区。"""
    plain = raw.get("stages")
    if plain is not None and not isinstance(plain, list):
        raise OsLabError("%s：stages 要写成列表" % MANIFEST)
    plain = list(plain or [])
    single = raw.get("boot")
    if plain and single:
        raise OsLabError("%s：boot 和 stages 只能写一个，多级引导用 stages" % MANIFEST)
    if single is not None:
        plain = [single]
    if not plain:
        raise OsLabError("%s：缺 stages（或单级的 boot）" % MANIFEST)
    if not all(isinstance(item, (str, dict)) for item in plain):
        raise OsLabError("%s：stages 每项是路径，或 { path = ..., addr = 0x... }" % MANIFEST)
    out = []
    for index, item in enumerate(plain):
        patch = item if isinstance(item, dict) else {"path": item}
        path = _string(patch, "path")
        if workspace.ext(path) not in ASM_OK:
            raise OsLabError("%s：stages 只收 %s" % (MANIFEST, " / ".join(ASM_OK)))
        addr = _number(patch, "addr", DEFAULT_BASE if index == 0 else 0, 0, KERNEL_MAX, 16)
        if index == 0 and not addr:
            raise OsLabError("%s：第一个 stage 是引导扇区，addr 不能是 0" % MANIFEST)
        out.append({"path": _join(rel, path), "addr": addr, "index": index})
    return out


def load(directory, base=None):
    """Read and validate the manifest; returns a normalised dict."""
    rel = workspace.safe(directory)
    raw_path = os.path.join(workspace.root(base), rel.replace("/", os.sep), MANIFEST)
    if not os.path.isfile(raw_path):
        raise OsLabError("这里没有 %s：%s" % (MANIFEST, rel or "."))
    try:
        with open(raw_path, "rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise OsLabError("%s 解析失败：%s" % (MANIFEST, exc)) from exc

    stale = sorted(raw.get("run") or {}) if isinstance(raw.get("run"), dict) else []
    if stale:
        raise OsLabError("%s：不再有 [run]（%s 这几项），按钮文字和入口暂停到运行配置里改"
                         % (MANIFEST, "、".join(stale)))
    unknown = sorted(key for key in raw if key not in KEYS and key != "run")
    if unknown:
        raise OsLabError("%s：不认识的键 %s，能写的是 %s"
                         % (MANIFEST, "、".join(unknown), " / ".join(KEYS)))

    qemu = raw.get("qemu") or {}
    if not isinstance(qemu, dict):
        raise OsLabError("%s：[qemu] 得是张表" % MANIFEST)
    bad_qemu = sorted(key for key in qemu if key not in QEMU_KEYS)
    if bad_qemu:
        raise OsLabError("%s：[qemu] 里不认识的键 %s，能写的是 %s"
                         % (MANIFEST, "、".join(bad_qemu), " / ".join(QEMU_KEYS)))

    kind = str(raw.get("kind", "")).lower()
    if kind not in KINDS:
        raise OsLabError("%s：kind 只能是 %s" % (MANIFEST, " / ".join(KINDS)))

    entry = _string(raw, "entry")
    if workspace.ext(entry) not in RUNNABLE:
        raise OsLabError("%s：entry 必须是 %s" % (MANIFEST, " / ".join(RUNNABLE)))

    build = _list(raw, "build")
    plan = {
        "dir": rel,
        "kind": kind,
        "entry": _join(rel, entry),
        "base": _number(raw, "base", DEFAULT_BASE, 0x500, DEFAULT_BASE, 16),
        "kernel": DEFAULT_KERNEL,
        "symbol": str(raw.get("symbol") or DEFAULT_SYMBOL).strip(),
        "build": build,
        "image": "",
        "elf": "",
        "map": "",
        "boot": "",
        "link": "",
        "stages": [],
        "sources": [],
        "cflags": _list(raw, "cflags"),
        "ldflags": _list(raw, "ldflags"),
        "includes": _list(raw, "includes"),
        "qemu": qemu,
    }
    for key in C_ONLY:
        if raw.get(key) and kind != "c":
            raise OsLabError("%s：%s 只有 C 工程用得上（kind = \"c\"）" % (MANIFEST, key))

    if not plan["symbol"].replace("_", "").isalnum():
        raise OsLabError("%s：symbol 要是符号名，比如 _start 或 startup_32" % MANIFEST)

    if build:
        plan["image"] = _join(rel, _string(raw, "image"))
        plan["elf"] = _join(rel, str(raw.get("elf") or "").strip())
        plan["map"] = _join(rel, str(raw.get("map") or "").strip())
        # image 是产物，第一次构建前还不存在，只要求入口在
        if not os.path.isfile(workspace.full(plan["entry"], base)):
            raise OsLabError("%s：找不到 %s" % (MANIFEST, plan["entry"]))
        return plan

    plan["kernel"] = _number(raw, "kernel", DEFAULT_KERNEL, 0, KERNEL_MAX, 16)
    if kind == "asm":            # stages 可选：写了就是自备引导链，不写就单文件汇编
        if raw.get("stages") or raw.get("boot"):
            plan["stages"] = _stages(raw, rel)
            plan["boot"] = plan["stages"][0]["path"]
    if kind == "c":
        plan["stages"] = _stages(raw, rel)
        plan["link"] = _join(rel, _string(raw, "link"))
        plan["boot"] = plan["stages"][0]["path"]
        sources = _list(raw, "sources") or [entry]
        plan["sources"] = [_join(rel, item) for item in sources]
        if plan["entry"] not in plan["sources"]:
            raise OsLabError("%s：entry 得在 sources 里，否则链接不到 %s"
                             % (MANIFEST, plan["symbol"]))
        for source in plan["sources"]:
            if workspace.ext(source) not in RUNNABLE:
                raise OsLabError("%s：sources 只收 %s" % (MANIFEST, " / ".join(RUNNABLE)))
    plan["map"] = _join(rel, str(raw.get("map") or "").strip())
    plan["elf"] = _join(rel, str(raw.get("elf") or "").strip())

    checked = [plan["entry"], *[item["path"] for item in plan["stages"]], *plan["sources"]]
    if plan["link"]:
        checked.append(plan["link"])
    for key in [item for item in checked if item]:
        if not os.path.isfile(workspace.full(key, base)):
            raise OsLabError("%s：找不到 %s" % (MANIFEST, key))
    return plan


def _string(raw, key):
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise OsLabError("%s：%s 必须是非空字符串" % (MANIFEST, key))
    return value.strip().lstrip("/")


def image_path(session_dir):
    return os.path.join(session_dir, "boot.img")
