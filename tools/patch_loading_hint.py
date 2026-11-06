"""Loading hint over the screen while the machine is not up yet."""
import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

# markup
h = root / "index.html"
s = h.read_text(encoding="utf-8")
s = s.replace('<div id="screenwrap"><canvas id="screen" width="720" height="478" '
              'tabindex="0"></canvas></div>',
              '<div id="screenwrap"><canvas id="screen" width="720" height="478" '
              'tabindex="0"></canvas><div id="screen-hint" class="open">'
              '<span class="spin"></span><span class="word">待机，点「运行」启动</span></div></div>')
h.write_text(s, encoding="utf-8", newline="\n")

# hint module
(root / "js/hint.js").write_text(
    '''const el = document.getElementById("screen-hint");
const word = el.querySelector(".word");

let frames = 0;

export function show(text) {
  if (text) word.textContent = text;
  el.classList.add("open");
}

export function hide() {
  el.classList.remove("open");
}

export function ready() {
  frames += 1;
  if (frames === 1) hide();
}

export function reset() {
  frames = 0;
}
''',
    encoding="utf-8",
    newline="\n",
)

# css
c = root / "styles/panels.css"
t = c.read_text(encoding="utf-8")
t = t.replace("#screenwrap {\n  flex: 0 1 auto;", "#screenwrap {\n  position: relative;\n  flex: 0 1 auto;")
t += """
#screen-hint {
  position: absolute;
  inset: 8px;
  display: none;
  place-content: center;
  justify-items: center;
  gap: 10px;
  background: #000;
  color: var(--dim);
  font-size: 13px;
  letter-spacing: .04em;
}
#screen-hint.open { display: grid; }
#screen-hint .spin {
  width: 22px;
  height: 22px;
  border: 2px solid var(--edge);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 900ms linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
"""
c.write_text(t, encoding="utf-8", newline="\n")

# panels.js drives the text from the session state
p = root / "js/panels.js"
u = p.read_text(encoding="utf-8")
u = u.replace('const statusEl = document.getElementById("status");',
              'const statusEl = document.getElementById("status");\n\nimport("./hint.js").catch(() => {});')
p.write_text(u, encoding="utf-8", newline="\n")
print("ok")
