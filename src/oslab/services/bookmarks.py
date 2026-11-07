"""Cross-file bookmarks: a line in a file you want to get back to.

Stored next to the user's settings, not inside the project, so a bookmark list
survives switching projects. Entries whose file disappeared stay listed and are
marked instead of being silently dropped.
"""
import json
import os

from ..core.errors import OsLabError
from . import workspace

NAME = "bookmarks.json"
LIMIT = 200


def _path(base=None):
    return os.path.join(workspace.root(base), NAME)


def load(base=None):
    try:
        with open(_path(base), encoding="utf-8") as fh:
            raw = json.load(fh).get("marks") or []
    except (OSError, ValueError):
        raw = []
    out = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        rel = str(row.get("file") or "").strip()
        try:
            line = int(row.get("line") or 0)
        except (TypeError, ValueError):
            continue
        if not rel or line <= 0:
            continue
        out.append({"file": rel, "line": line, "text": str(row.get("text") or "")[:120],
                    "missing": not os.path.isfile(workspace.full(rel, base))})
    return out[:LIMIT]


def _write(rows, base=None):
    with open(_path(base), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"marks": [{k: row[k] for k in ("file", "line", "text")} for row in rows]},
                  fh, ensure_ascii=False, indent=1)


def toggle(payload, base=None):
    """同一行再按一次就取消；返回整个清单和这一行现在的状态。"""
    rel = str(payload.get("file") or "").strip()
    if not rel or not workspace.safe(rel):
        raise OsLabError("书签得写上是哪个文件")
    try:
        line = int(payload.get("line"))
    except (TypeError, ValueError):
        raise OsLabError("书签得写上是第几行") from None
    if line <= 0:
        raise OsLabError("行号从 1 开始")
    rows = load(base)
    now = any(row["file"] == rel and row["line"] == line for row in rows)
    if now:
        rows = [row for row in rows if not (row["file"] == rel and row["line"] == line)]
    else:
        if len(rows) >= LIMIT:
            raise OsLabError("书签最多 %d 条，先删几条" % LIMIT)
        rows.insert(0, {"file": rel, "line": line, "text": str(payload.get("text") or "")[:120],
                        "missing": False})
    _write(rows, base)
    return {"marks": load(base), "on": not now}


def remove(payload, base=None):
    rel = str(payload.get("file") or "").strip()
    line = payload.get("line")
    rows = [row for row in load(base)
            if not (row["file"] == rel and (line is None or row["line"] == int(line)))]
    _write(rows, base)
    return {"marks": load(base)}


def clear(base=None):
    _write([], base)
    return {"marks": []}
