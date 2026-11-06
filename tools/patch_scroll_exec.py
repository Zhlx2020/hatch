import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

p = root / "tools/editor_entry.js"
s = p.read_text(encoding="utf-8")
s = s.replace('''    markLine(line) {
      view.dispatch({ effects: setExec.of(line || 0) });
    },''',
'''    markLine(line) {
      view.dispatch({ effects: setExec.of(line || 0) });
    },
    scrollTo(line) {
      try {
        const info = view.state.doc.line(Math.min(line, view.state.doc.lines));
        view.dispatch({ effects: EditorView.scrollIntoView(info.from, { y: "center" }) });
      } catch {
        /* 行号超出范围时不动 */
      }
    },''')
p.write_text(s, encoding="utf-8", newline="\n")

e = root / "src/oslab/assets/ui/js/editor.js"
t = e.read_text(encoding="utf-8")
t = t.replace('''export function markLine(line) {
  view.markLine(line);
}''',
'''let lastMark = 0;

export function markLine(line) {
  if (line === lastMark) return;
  lastMark = line;
  view.markLine(line);
  if (line) view.scrollTo(line);
}''')
e.write_text(t, encoding="utf-8", newline="\n")
print("ok")
