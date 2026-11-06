"""Assemble without booting, so the editor can lint on save."""
import os
import re
import uuid

from .. import config
from ..core.errors import AssembleError
from . import build

LINE = re.compile(r"^.*?:(\d+)[: ]\s*(?:error|warning)?:?\s*(.*)$")


def check(path, text):
    if not build.supported(path):
        return {"ok": True, "skipped": True, "errors": []}
    scratch = os.path.join(config.RUN_DIR, "check")
    os.makedirs(scratch, exist_ok=True)
    image = os.path.join(scratch, uuid.uuid4().hex[:8] + ".img")
    size = 0
    try:
        build.build(text, path, image)
        size = os.path.getsize(image)
    except AssembleError as exc:
        return {"ok": False, "errors": _parse(str(exc))}
    finally:
        for suffix in ("", ".asm", ".dis.intel", ".dis.att", ".lst"):
            try:
                os.remove(image + suffix)
            except OSError:
                pass
    return {"ok": True, "errors": [], "size": size}


def _parse(message):
    errors = []
    for raw in message.splitlines():
        text = raw.strip()
        if not text:
            continue
        match = LINE.match(text)
        if match:
            errors.append({"line": int(match.group(1)), "message": match.group(2)})
        else:
            errors.append({"line": 0, "message": text})
    return errors
