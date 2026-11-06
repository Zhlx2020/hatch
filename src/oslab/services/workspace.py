"""Workspace tree: nested files and directories under `config.WORKSPACE`.

Paths always travel as `/`-separated relative strings; every segment is
validated so a request can never escape the workspace root.
"""
import os
import shutil

from .. import config
from ..core.errors import OsLabError

SEGMENT = r"^[A-Za-z0-9_.-]{1,64}$"
KINDS = {".asm", ".inc", ".c", ".h", ".toml", ".txt", ".md"}
RUNNABLE = {".asm", ".c"}

TEMPLATES = {
    ".asm": "bits 16\norg 0x7c00\n\n    hlt\n\ntimes 510-($-$$) db 0\ndw 0xaa55\n",
    ".inc": "; 供 %include 使用的片段\n",
    ".c": "/* 预留：C 语言混合开发 */\n",
    ".h": "#pragma once\n",
    ".toml": '',
    ".txt": "",
    ".md": "",
}


def root(base=None):
    return os.path.abspath(base or config.WORKSPACE)


def safe(path):
    """Normalise and validate a relative path, returning `/`-joined form."""
    if path is None:
        raise OsLabError("缺路径")
    clean = path.replace("\\", "/").strip("/")
    if not clean:
        return ""
    segments = [part for part in clean.split("/") if part and part != "."]
    if not segments:
        return ""
    clean = "/".join(segments)
    for segment in segments:
        if not segment or segment in (".", ".."):
            raise OsLabError("非法路径段：%s" % path)
        if not _ok_segment(segment):
            raise OsLabError("非法字符：%s" % segment)
    return clean


def _ok_segment(segment):
    import re

    return bool(re.match(SEGMENT, segment)) and ".." != segment


def ext(name):
    return os.path.splitext(name)[1].lower()


def full(path, base=None):
    target = os.path.abspath(os.path.join(root(base), safe(path)))
    if not target.startswith(root(base)):
        raise OsLabError("越界路径：%s" % path)
    return target


def tree(base=None):
    """Recursive listing, directories first, for the file rail."""
    return _walk(root(base), "")


def _walk(directory, prefix):
    out = []
    try:
        names = sorted(os.listdir(directory), key=lambda n: (not os.path.isdir(
            os.path.join(directory, n)), n.lower()))
    except OSError:
        return out
    for name in names:
        absolute = os.path.join(directory, name)
        rel = prefix + name
        if os.path.isdir(absolute):
            out.append({"path": rel, "name": name, "kind": "dir",
                        "children": _walk(absolute, rel + "/")})
            continue
        suffix = ext(name)
        if suffix not in KINDS:
            continue
        out.append({"path": rel, "name": name, "kind": "file", "ext": suffix,
                    "size": os.path.getsize(absolute),
                    "runnable": suffix in RUNNABLE})
    return out


def read(path, base=None):
    try:
        with open(full(path, base), encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        raise OsLabError("读不到：%s" % path) from exc


def write(path, text, base=None):
    target = full(path, base)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text)
    return path


def touch(path, base=None):
    target = full(path, base)
    if os.path.exists(target):
        raise OsLabError("已存在：%s" % path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    suffix = ext(path)
    if suffix not in KINDS:
        raise OsLabError("不支持的类型：%s" % path)
    with open(target, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(TEMPLATES.get(suffix, ""))
    return path


def mkdir(path, base=None):
    target = full(path, base)
    if os.path.exists(target):
        raise OsLabError("已存在：%s" % path)
    os.makedirs(target)
    return path


def rename(path, name, base=None):
    if not _ok_segment(name):
        raise OsLabError("非法名字：%s" % name)
    source = full(path, base)
    if not os.path.exists(source):
        raise OsLabError("找不到：%s" % path)
    target = os.path.join(os.path.dirname(source), name)
    if os.path.exists(target):
        raise OsLabError("重名：%s" % name)
    os.rename(source, target)
    parent = os.path.dirname(safe(path).replace("/", os.sep))
    return (parent.replace(os.sep, "/") + "/" + name).lstrip("/")


def move(path, directory, base=None):
    source = full(path, base)
    target_dir = full(directory, base) if directory else root(base)
    if not os.path.exists(source):
        raise OsLabError("找不到：%s" % path)
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, os.path.basename(source))
    if os.path.abspath(target) == os.path.abspath(source):
        return safe(path)
    if os.path.exists(target):
        raise OsLabError("目标已存在：%s" % os.path.basename(source))
    shutil.move(source, target)
    rel = os.path.relpath(target, root(base)).replace(os.sep, "/")
    return rel


def remove(path, base=None):
    target = full(path, base)
    if not os.path.exists(target):
        raise OsLabError("找不到：%s" % path)
    if os.path.isdir(target):
        shutil.rmtree(target)
    else:
        os.remove(target)
    return path


def entry_file(base=None):
    """The file a bare 'run' uses: first runnable in tree order."""
    for item in _flatten(tree(base)):
        if item["runnable"]:
            return item["path"]
    return ""


def _flatten(nodes):
    for node in nodes:
        if node["kind"] == "dir":
            yield from _flatten(node["children"])
        else:
            yield node


def list_files(base=None):
    """Flat list kept for callers that only need runnable names."""
    return [{"name": node["path"], "size": node.get("size", 0)}
            for node in _flatten(tree(base)) if node["runnable"]]
