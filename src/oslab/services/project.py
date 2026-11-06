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

    kind = str(raw.get("kind", "")).lower()
    if kind not in KINDS:
        raise OsLabError("%s：kind 只能是 %s" % (MANIFEST, " / ".join(KINDS)))

    entry = _string(raw, "entry")
    if workspace.ext(entry) not in (".asm", ".c"):
        raise OsLabError("%s：entry 必须是 .asm 或 .c" % MANIFEST)

    plan = {
        "dir": rel,
        "kind": kind,
        "entry": _join(rel, entry),
        "base": int(raw.get("base", DEFAULT_BASE)),
        "boot": "",
        "link": "",
        "sources": [],
    }
    if kind == "c":
        plan["boot"] = _join(rel, _string(raw, "boot"))
        plan["link"] = _join(rel, _string(raw, "link"))
        sources = raw.get("sources") or [entry]
        plan["sources"] = [_join(rel, str(item)) for item in sources]

    for key in [plan["entry"], plan["boot"], plan["link"], *plan["sources"]]:
        if not key:
            continue
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
