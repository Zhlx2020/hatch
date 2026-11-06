import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

p = root / "index.html"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '<div class="body"><textarea id="code" spellcheck="false" autocomplete="off"></textarea></div>',
    '<div class="body" id="editor-body"><div id="editor-host"></div>'
    '<div id="problems"></div></div>',
)
p.write_text(s, encoding="utf-8", newline="\n")

a = root / "js/api.js"
t = a.read_text(encoding="utf-8")
if "export const check" not in t:
    t += '\nexport const check = (path, text) => post("/api/check", { path, text });\n'
a.write_text(t, encoding="utf-8", newline="\n")

c = root / "styles/layout.css"
u = c.read_text(encoding="utf-8")
u += """
#editor-body { display: flex; flex-direction: column; min-height: 0; }
#editor-host { flex: 1; min-height: 0; overflow: hidden; }
#editor-host .cm-editor { height: 100%; }
#problems {
  display: none;
  max-height: 30%;
  overflow: auto;
  border-top: 1px solid var(--edge);
  padding: 4px 8px;
  font: 12px/1.6 ui-monospace, Consolas, monospace;
  color: var(--danger);
}
#problems.open { display: block; }
#problems .problem { white-space: pre-wrap; }
#problems .at {
  padding: 0 4px;
  margin-right: 4px;
  border-color: transparent;
  color: var(--danger);
  font: inherit;
}
"""
c.write_text(u, encoding="utf-8", newline="\n")
print("ok")
