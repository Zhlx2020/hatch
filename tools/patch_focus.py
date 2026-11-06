import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

# 1) 面板重绘时保住输入框的焦点和已输入内容
d = root / "src/oslab/assets/ui/js/detail.js"
s = d.read_text(encoding="utf-8")
s = s.replace('''function commit() {
  if (!stage) return;
  bodyEl.replaceChildren(stage);
  stage = null;
}''',
'''function commit() {
  if (!stage) return;
  // 面板每 700 毫秒重绘一次，正在输入的框不能被换掉。
  const active = document.activeElement;
  const editing = active && bodyEl.contains(active) && active.tagName === "INPUT"
    ? active : null;
  const inputs = [...bodyEl.querySelectorAll("input")];
  const index = editing ? inputs.indexOf(editing) : -1;
  const value = editing ? editing.value : "";
  const start = editing ? editing.selectionStart : 0;
  const end = editing ? editing.selectionEnd : 0;
  bodyEl.replaceChildren(stage);
  stage = null;
  if (index < 0) return;
  const again = bodyEl.querySelectorAll("input")[index];
  if (!again) return;
  again.value = value;
  again.focus();
  try {
    again.setSelectionRange(start, end);
  } catch (_) {
    /* number 类型不支持选区 */
  }
}''')

# 2) 写回寄存器也每 700ms 重绘，正在改的框要留住
s = s.replace('''export function install() {
  tabsEl.addEventListener("click"''',
'''export function install() {
  bodyEl.addEventListener("focusin", (ev) => {
    const input = ev.target.closest("input");
    if (input) input.dataset.editing = "1";
  });
  bodyEl.addEventListener("focusout", (ev) => {
    const input = ev.target.closest("input");
    if (input) delete input.dataset.editing;
  });
  tabsEl.addEventListener("click"''')
d.write_text(s, encoding="utf-8", newline="\n")

# 3) 去掉 RSP 抓包日志
r = root / "src/oslab/backend/qemu/rsp.py"
t = r.read_text(encoding="utf-8")
t = t.replace('        _dbg(">> " + body.decode("ascii", "replace")[:40])\n', "")
t = t.replace('                _dbg("<< " + body.decode("ascii", "replace")[:40])\n', "")
t = t.replace('''def _dbg(text):
    import os
    import time

    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))), ".run", "rsp.log")
    try:
        with open(path, "a") as fh:
            fh.write("%.3f %s\\n" % (time.time(), text))
    except OSError:
        pass


''', "")
r.write_text(t, encoding="utf-8", newline="\n")
print("ok")
