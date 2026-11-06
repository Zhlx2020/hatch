import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

p = root / "index.html"
s = p.read_text(encoding="utf-8")
s = s.replace('<link rel="stylesheet" href="/ui/styles/panels.css" />',
              '<link rel="stylesheet" href="/ui/styles/panels.css" />\n'
              '<link rel="stylesheet" href="/ui/styles/detail.css" />')
p.write_text(s, encoding="utf-8", newline="\n")

b = root / "js/boot.js"
t = b.read_text(encoding="utf-8")
t = t.replace('import * as api from "./api.js";',
              'import * as api from "./api.js";\nimport * as detail from "./detail.js";')
t = t.replace("editor.install();", "editor.install();\ndetail.install();")
t = t.replace('document.getElementById("run").addEventListener("click", boot);',
              '''document.getElementById("run").addEventListener("click", boot);
for (const button of document.querySelectorAll("[data-open]")) {
  button.addEventListener("click", () => detail.open(button.dataset.open));
}
for (const box of ["regs", "mem", "disasm"]) {
  document.getElementById(box).addEventListener("dblclick", () => detail.open(
    box === "disasm" ? "dis" : box));
}''')
b.write_text(t, encoding="utf-8", newline="\n")
print("ok")
