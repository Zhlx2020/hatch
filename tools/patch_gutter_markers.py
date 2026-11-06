import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tools/editor_entry.js"
s = p.read_text(encoding="utf-8")

s = s.replace('''const bpDot = new BpDot();''',
'''const bpDot = new BpDot();
const bpBlank = new (class extends GutterMarker {})();''')

s = s.replace('''    build(view) {
      const lines = [...view.state.field(bpLines)].sort((a, b) => a - b);
      if (!lines.length) return RangeSet.empty;
      const builder = new RangeSetBuilder();
      let previous = 0;
      for (const number of lines) {
        const info = view.state.doc.line(Math.min(Math.max(number, 1), view.state.doc.lines));
        if (info.from === previous) continue;
        builder.add(info.from, info.from, bpDot);
        previous = info.from;
      }
      return builder.finish();
    }''',
'''    // 每一行都给一个标记：没有断点的用空标记，gutter 才会为整屏建出可点行
    build(view) {
      const marked = new Set(view.state.field(bpLines));
      const builder = new RangeSetBuilder();
      for (const range of view.visibleRanges) {
        let pos = range.from;
        while (pos <= range.to) {
          const line = view.state.doc.lineAt(pos);
          builder.add(line.from, line.from, marked.has(line.number) ? bpDot : bpBlank);
          pos = line.to + 1;
        }
      }
      return builder.finish();
    }''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
