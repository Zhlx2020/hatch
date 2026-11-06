import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/index.html"
s = p.read_text(encoding="utf-8")
s = s.replace('<div id="settings">', '''<div id="templates">
  <div id="templates-head">
    <span>从模板新建</span>
    <span class="grow"></span>
    <button id="templates-close">关闭</button>
  </div>
  <div id="templates-body"></div>
</div>

<div id="settings">''')
p.write_text(s, encoding="utf-8", newline="\n")

c = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/styles/detail.css"
t = c.read_text(encoding="utf-8")
t += """
#templates {
  position: fixed;
  top: 18vh;
  left: 50%;
  transform: translateX(-50%);
  width: 420px;
  z-index: 70;
  display: none;
  flex-direction: column;
  padding: 10px;
  background: var(--panel);
  border: 1px solid var(--edge);
  border-radius: 6px;
  box-shadow: 0 18px 40px #0009;
}
#templates.open { display: flex; }
#templates-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--edge);
}
#templates-head .grow { flex: 1; }
#templates-body { padding-top: 8px; display: flex; flex-direction: column; gap: 6px; }
#templates-body button { text-align: left; padding: 8px 10px; }
#templates-body .summary { display: block; color: var(--dim); font-size: 12.5px; margin-top: 3px; }
"""
c.write_text(t, encoding="utf-8", newline="\n")

a = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js/api.js"
u = a.read_text(encoding="utf-8")
u += """
export const templates = () => json("/api/templates");
export const applyTemplate = (name, dir) => post("/api/template", { name, dir });
"""
a.write_text(u, encoding="utf-8", newline="\n")
print("ok")
