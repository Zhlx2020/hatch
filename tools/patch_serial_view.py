import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

i = root / "src/oslab/assets/ui/index.html"
t = i.read_text(encoding="utf-8")
t = t.replace('''<div id="screen-hint" class="open"><span class="spin"></span><span class="word">待机，点「运行」启动</span></div></div>''',
'''<div id="screen-hint" class="open"><span class="spin"></span><span class="word">待机，点「运行」启动</span></div>
      <pre id="serial-view" hidden></pre></div>''')
i.write_text(t, encoding="utf-8", newline="\n")

c = root / "src/oslab/assets/ui/styles/panels.css"
s = c.read_text(encoding="utf-8")
s += """
/* 串口模板没有画面，就把屏幕那块让给串口文本 */
#serial-view {
  position: absolute;
  inset: 0;
  margin: 0;
  padding: 10px 12px;
  overflow: hidden;
  font: 13px/1.35 Consolas, "Courier New", monospace;
  color: #9fe6a0;
  background: #06090a;
  white-space: pre-wrap;
  word-break: break-all;
}
body.serial-mode #screen { visibility: hidden; }
"""
c.write_text(s, encoding="utf-8", newline="\n")

p = root / "src/oslab/assets/ui/js/panels.js"
u = p.read_text(encoding="utf-8")
u = u.replace('''// 串口不再占用界面：客户机写 COM1 的文本仍由 /api/serial 保留，脚本可用。
export async function loadSerial() {}

export function clearSerial() {}''',
'''// 只有在串口模板下才把串口当屏幕：其余时候文本仍留在 /api/serial 给脚本用。
const serialView = document.getElementById("serial-view");
let serialText = "";

export function serialMode(on) {
  document.body.classList.toggle("serial-mode", !!on);
  serialView.hidden = !on;
  if (on) serialView.scrollTop = serialView.scrollHeight;
}

export async function loadSerial() {}

export function clearSerial() {
  serialText = "";
  if (serialView) serialView.textContent = "";
}

function feedSerial(text) {
  if (!text) return;
  serialText = (serialText + text).slice(-4000);
  if (serialView) {
    serialView.textContent = serialText;
    serialView.scrollTop = serialView.scrollHeight;
  }
}''')
p.write_text(u, encoding="utf-8", newline="\n")
print("ok")
