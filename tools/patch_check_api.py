import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

# 1. checker service ---------------------------------------------------
(root / "services/checker.py").write_text(
    '''"""Assemble without booting, so the editor can lint on save."""
import os
import re
import uuid

from .. import config
from ..core.errors import AssembleError
from . import build, workspace

LINE = re.compile(r"^.*?:(\\d+):\\s*(?:error|warning)?:?\\s*(.*)$")


def check(path, text):
    scratch = os.path.join(config.RUN_DIR, "check")
    os.makedirs(scratch, exist_ok=True)
    image = os.path.join(scratch, uuid.uuid4().hex[:8] + ".img")
    try:
        build.build(text, path, image)
    except AssembleError as exc:
        errors = []
        for raw in str(exc).splitlines():
            match = LINE.match(raw.strip())
            if match:
                errors.append({"line": int(match.group(1)), "message": match.group(2)})
            elif raw.strip():
                errors.append({"line": 0, "message": raw.strip()})
        return {"ok": False, "errors": errors}
    finally:
        for suffix in ("", ".asm", ".dis"):
            try:
                os.remove(image + suffix)
            except OSError:
                pass
    return {"ok": True, "errors": [], "size": os.path.getsize(image) if False else 0}
''',
    encoding="utf-8",
    newline="\n",
)

# 2. handlers ----------------------------------------------------------
p = root / "web/handlers.py"
s = p.read_text(encoding="utf-8")
s = s.replace("from ..services import workspace",
              "from ..services import checker, workspace")
s = s.replace("# control -------------------------------------------------------------",
              '''async def check(request):
    body = await request.json()
    path = body.get("path", "")
    try:
        result = await asyncio.to_thread(checker.check, path, body.get("text", ""))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(result)


# control -------------------------------------------------------------''')
p.write_text(s, encoding="utf-8", newline="\n")

# 3. route -------------------------------------------------------------
r = root / "web/routes.py"
t = r.read_text(encoding="utf-8")
t = t.replace('    ("POST", "/api/run", handlers.run),\n',
              '    ("POST", "/api/check", handlers.check),\n    ("POST", "/api/run", handlers.run),\n')
r.write_text(t, encoding="utf-8", newline="\n")
print("ok")
