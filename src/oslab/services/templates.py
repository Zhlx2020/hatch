"""Start a project from a bundled template.

Templates live in `templ/` inside the package and are copied into the workspace;
each one carries its own manifest, so the copy is immediately runnable.
"""
import os
import shutil

from .. import config
from ..core.errors import OsLabError
from . import workspace

ROOT = os.path.join(config.PROJECT, "templ")


def entries():
    out = []
    if not os.path.isdir(ROOT):
        return out
    for name in sorted(os.listdir(ROOT)):
        directory = os.path.join(ROOT, name)
        if not os.path.isdir(directory):
            continue
        readme = os.path.join(directory, "README.md")
        summary = ""
        if os.path.isfile(readme):
            with open(readme, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        summary = line
                        break
        out.append({"name": name, "summary": summary})
    return out


def apply(name, target, base=None):
    """Copy template `name` to `target` (a directory path inside the workspace)."""
    safe_name = os.path.basename(str(name))
    source = os.path.join(ROOT, safe_name)
    if not os.path.isdir(source):
        raise OsLabError("没有这个模板：%s" % name)
    rel = workspace.safe(target)
    if not rel:
        raise OsLabError("要指定目标目录")
    destination = workspace.full(rel, base)
    if os.path.exists(destination) and os.listdir(destination):
        raise OsLabError("目标不是空的：%s" % rel)
    os.makedirs(destination, exist_ok=True)
    for item in os.listdir(source):
        src = os.path.join(source, item)
        dst = os.path.join(destination, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    entry = ""
    manifest = os.path.join(destination, "oslab.toml")
    if os.path.isfile(manifest):
        try:
            import tomllib

            with open(manifest, "rb") as fh:
                entry = str(tomllib.load(fh).get("entry") or "")
        except Exception:
            entry = ""
    return {"dir": rel, "entry": (rel + "/" + entry).lstrip("/") if entry else ""}
