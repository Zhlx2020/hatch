import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js"

q = root / "screen.js"
t = q.read_text(encoding="utf-8")
t = t.replace(
    'import * as socket from "./socket.js";\nimport { releaseAll } from "./input.js";',
    'import * as socket from "./socket.js";',
)
t = t.replace(
    "    statusEl.textContent = \"画面已连接\";\n    releaseAll();\n    request();",
    "    statusEl.textContent = \"画面已连接\";\n"
    "    import(\"./input.js\").then((m) => m.releaseAll()).catch(() => {});\n"
    "    request();",
)
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
