import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js"

p = root / "input.js"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "export function install() {",
    """export function releaseAll() {
  for (let code = 0x20; code <= 0x7e; code += 1) keyEvent(false, code);
  for (const sym of Object.values(NAMED)) keyEvent(false, sym);
}

export function install() {""",
)
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "screen.js"
t = q.read_text(encoding="utf-8")
t = t.replace(
    'import * as socket from "./socket.js";',
    'import * as socket from "./socket.js";\nimport { releaseAll } from "./input.js";',
)
t = t.replace(
    '    statusEl.textContent = "画面已连接";\n    request();',
    '    statusEl.textContent = "画面已连接";\n    releaseAll();\n    request();',
)
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
