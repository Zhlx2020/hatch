"""Find where a name is declared, so the editor can jump there.

Only two shapes matter here: a C function/宏/类型 and an assembly label. The
search is textual on purpose — a half-written file still jumps, and nothing has
to compile first. Definitions rank above declarations, and the current file
ranks above the rest.
"""
import os
import re

from ..core.errors import OsLabError
from . import project, workspace

LIMIT = 20
C_SUFFIX = (".c", ".h")
ASM_SUFFIX = (".asm", ".inc")
C_WORD = re.compile(r"^[A-Za-z_]\w*$")
ASM_WORD = re.compile(r"^[A-Za-z_.$][\w.$]*$")


def _c_patterns(word):
    body = r"\b" + re.escape(word) + r"\s*\("
    return [
        # 带分号收尾的是声明，不带的是定义：先判声明，免得抢在定义前面
        (re.compile(r"^[A-Za-z_][\w \t\*]*" + body + r"[^;{]*;\s*$"), "函数声明", False),
        (re.compile(r"^[A-Za-z_][\w \t\*]*" + body), "函数定义", True),
        (re.compile(r"^\s*#\s*define\s+" + re.escape(word) + r"\b"), "宏", False),
        (re.compile(r"\btypedef\b[^;]*\b" + re.escape(word) + r"\s*;"), "类型", False),
        (re.compile(r"^[A-Za-z_][\w \t\*]*\b" + re.escape(word) + r"\s*(?:\[|;|=|,)"), "变量", False),
    ]


def _asm_patterns(word):
    body = re.escape(word)
    return [
        (re.compile(r"^\s*(?:global|extern)?\s*" + body + r"\s*:"), "标签", True),
        (re.compile(r"^\s*" + body + r"\s+(?:equ|db|dw|dd|dq)\b", re.I), "数据", True),
    ]


def _scan(text, patterns, kind):
    found = []
    for index, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\r")
        for pattern, label, definition in patterns:
            if pattern.search(line):
                found.append({"line": index, "kind": label, "def": definition,
                              "text": line.strip()[:120], "by": kind})
                break
    return found


def _candidates(files, word, kind):
    patterns = _c_patterns(word) if kind == "c" else _asm_patterns(word)
    out = []
    for order, rel in enumerate(files):
        try:
            with open(workspace.full(rel), encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for hit in _scan(text, patterns, kind):
            hit["file"] = rel
            hit["rank"] = (0 if hit["def"] else 1, order)
            out.append(hit)
    out.sort(key=lambda row: (row["rank"], row["line"]))
    return out[:LIMIT]


def _siblings(path, suffixes):
    """先本文件、同目录，再本工程，最后整个工作区。"""
    own = os.path.dirname(path)
    ordered = [path] if path.endswith(suffixes) else []
    seen = set(ordered)
    roots = [""]
    owner = project.find(path)
    if owner:
        roots.insert(0, owner)
    for root in roots:
        base = workspace.full(root) if root else workspace.root()
        near, far = [], []
        for folder, dirs, names in os.walk(base):
            dirs[:] = sorted(d for d in dirs
                             if d not in (".git", ".work", ".run", "node_modules"))
            rel_folder = os.path.relpath(folder, workspace.root()).replace(os.sep, "/")
            rel_folder = "" if rel_folder == "." else rel_folder
            for name in sorted(names):
                if not name.endswith(suffixes):
                    continue
                rel = (rel_folder + "/" + name) if rel_folder else name
                if rel not in seen:
                    (near if rel_folder == own else far).append(rel)
        for rel in near + far:
            seen.add(rel)
            ordered.append(rel)
        if len(ordered) > 400:
            break
    return ordered


def declarations(path, word, base=None):
    if not word:
        raise OsLabError("光标下面没有名字")
    kind = "c" if path.lower().endswith(C_SUFFIX) else "asm"
    if kind == "c" and not C_WORD.match(word):
        raise OsLabError("这不是个能跳的 C 名字")
    if kind == "asm" and not ASM_WORD.match(word):
        raise OsLabError("这不是个能跳的汇编标签")
    rows = _candidates(_siblings(path, C_SUFFIX if kind == "c" else ASM_SUFFIX), word, kind)
    return {"word": word, "kind": kind, "hits": rows,
            "files_scanned": 0 if not rows else len({row["file"] for row in rows})}
