import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

# --- index.html: 去掉串口面板 ---------------------------------------
p = root / "index.html"
s = p.read_text(encoding="utf-8")
s = s.replace('    <section class="pane"><h2>串口</h2><pre id="serial"></pre></section>\n', "")
p.write_text(s, encoding="utf-8", newline="\n")

# --- panels.js: 串口元素可以不存在 ----------------------------------
j = root / "js/panels.js"
t = j.read_text(encoding="utf-8")
t = t.replace('const serialEl = document.getElementById("serial");\n', "")
t = t.replace('''  if (snap.serial) {
    serialEl.textContent += snap.serial;
    serialEl.scrollTop = serialEl.scrollHeight;
  }''', "")
t = t.replace('''export async function loadSerial() {
  const res = await fetch("/api/serial");
  const data = await res.json();
  if (data.text) {
    serialEl.textContent = data.text;
    serialEl.scrollTop = serialEl.scrollHeight;
  }
}

export function clearSerial() {
  serialEl.textContent = "";
}''', '''// 串口不再占用界面：客户机写 COM1 的文本仍由 /api/serial 保留，脚本可用。
export async function loadSerial() {}

export function clearSerial() {}''')
j.write_text(t, encoding="utf-8", newline="\n")

# --- layout.css: 侧栏字号与文件/目录区分、编辑器滚动条 ---------------
c = root / "styles/layout.css"
u = c.read_text(encoding="utf-8")
u = u.replace("""#files .body { padding: 6px 4px; user-select: none; }
#tree .row {
  display: flex;
  align-items: center;
  gap: 5px;
  height: 22px;
  padding-right: 6px;
  border: 1px solid transparent;
  border-radius: 3px;
  white-space: nowrap;
  overflow: hidden;
}
#tree .row .icon { width: 11px; color: var(--dim); flex: none; text-align: center; }
#tree .row .label { overflow: hidden; text-overflow: ellipsis; }
#tree .row:hover { background: color-mix(in srgb, var(--edge) 40%, transparent); }
#tree .row.active { border-color: var(--accent); color: var(--accent); }
#tree .row.dir .label { color: var(--fg); font-weight: 600; letter-spacing: .02em; }""",
"""#files .body { padding: 6px 4px; user-select: none; font-size: 13px; }
#tree .row {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 26px;
  padding-right: 6px;
  border: 1px solid transparent;
  border-radius: 3px;
  white-space: nowrap;
  overflow: hidden;
  cursor: pointer;
}
#tree .row .icon {
  width: 14px;
  flex: none;
  text-align: center;
  font-size: 11px;
  color: var(--dim);
}
#tree .row .label { overflow: hidden; text-overflow: ellipsis; }
#tree .row:hover { background: color-mix(in srgb, var(--edge) 40%, transparent); }
#tree .row.active { border-color: var(--accent); color: var(--accent); }
#tree .row.dir .icon { color: var(--accent); }
#tree .row.dir .label { color: var(--text); font-weight: 600; letter-spacing: .02em; }
#tree .row.file .icon { color: var(--dim); }
#tree .row.file .label { color: var(--dim); }
#tree .row.file.asm .label { color: var(--text); }
#tree .row.file .ext { color: var(--dim); font-size: 10px; letter-spacing: .06em; }""")
u = u.replace("#editor-host .cm-editor { height: 100%; }",
"""#editor-host .cm-editor { height: 100%; }
#editor-host .cm-scroller { scrollbar-width: none; }
#editor-host .cm-scroller::-webkit-scrollbar { width: 0; height: 0; }""")
c.write_text(u, encoding="utf-8", newline="\n")
print("ok")
