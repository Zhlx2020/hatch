import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"


def patch(rel, pairs):
    p = root / rel
    s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        assert old in s, (rel, old)
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8", newline="\n")


patch("web/routes.py", [(
    '    ("POST", "/api/cont", handlers.cont),',
    '    ("POST", "/api/cont", handlers.cont),\n    ("POST", "/api/pause", handlers.pause),',
)])

patch("web/handlers.py", [(
    "async def reset(_request):",
    "async def pause(_request):\n    return await _action(lambda s: s.pause())\n\n\nasync def reset(_request):",
)])

patch("assets/ui/js/api.js", [(
    "export const reset =",
    'export const pause = () => post("/api/pause");\nexport const reset =',
)])

patch("assets/ui/js/boot.js", [
    ('const CONTROLS = ["run", "pause", "step", "step-over", "reset"]',
     'const CONTROLS = ["run", "pause", "cont", "step", "step-over", "reset"]'),
    ('document.getElementById("pause").addEventListener("click", () => guarded(api.cont));',
     'document.getElementById("pause").addEventListener("click", () => guarded(api.pause));\n'
     'document.getElementById("cont").addEventListener("click", () => guarded(api.cont));'),
])

patch("assets/ui/index.html", [(
    '<button id="pause">继续</button>',
    '<button id="pause">暂停</button>\n  <button id="cont">继续</button>',
)])
print("ok")
