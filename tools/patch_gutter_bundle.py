import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tools/editor_entry.js"
s = p.read_text(encoding="utf-8")

# import gutter + RangeSetBuilder
s = s.replace("  highlightActiveLineGutter,", "  highlightActiveLineGutter,\n  gutter,\n  GutterMarker,")
if "RangeSetBuilder" not in s:
    s = s.replace('} from "@codemirror/view";', '  RangeSetBuilder,\n} from "@codemirror/view";') if False else s

# breakpoint state + plugin
s = s.replace('''function words() {''',
'''// 行断点：字段存行号，gutter 画红点，点击交给面板去解析地址
const setBps = StateEffect.define();

const bpLines = StateField.define({
  create: () => [],
  update(value, tr) {
    for (const effect of tr.effects) {
      if (effect.is(setBps)) value = effect.value;
    }
    return value;
  },
});

class BpDot extends GutterMarker {
  toDOM() {
    const dot = document.createElement("span");
    dot.className = "cm-bpDot";
    return dot;
  }
}

const bpDot = new BpDot();

const bpMarkers = ViewPlugin.fromClass(
  class {
    constructor(view) {
      this.markers = this.build(view);
    }
    update(update) {
      if (update.docChanged || update.viewportChanged
        || update.state.field(bpLines) !== update.startState.field(bpLines)) {
        this.markers = this.build(update.view);
      }
    }
    build(view) {
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
    }
  },
  { markers: (value) => value.markers },
);

function words() {''')

# create(): options + extensions + api
s = s.replace("export function create(parent, { onSave, onChange } = {}) {",
              "export function create(parent, { onSave, onChange, onToggleLine } = {}) {")
s = s.replace('''      execField,
      execPlugin,''',
'''      execField,
      execPlugin,
      bpLines,
      bpMarkers,
      gutter({
        class: "cm-bpGutter",
        markers: (view) => view.plugin(bpMarkers)?.markers ?? RangeSet.empty,
        domEventHandlers: {
          mousedown(view, line, ev) {
            ev.preventDefault();
            if (onToggleLine) onToggleLine(view.state.doc.lineAt(line.from).number);
            return true;
          },
        },
      }),''')
s = s.replace('''    markLine(line) {
      view.dispatch({ effects: setExec.of(line || 0) });
    },''',
'''    markLine(line) {
      view.dispatch({ effects: setExec.of(line || 0) });
    },
    breakpoints() {
      return [...view.state.field(bpLines)];
    },
    setBreakpoints(lines) {
      view.dispatch({ effects: setBps.of([...(lines || [])]) });
    },''')

# 主题
s = s.replace('".cm-gutters": { background: "transparent", border: "0", color: "#4a555f" },',
              '".cm-gutters": { background: "transparent", border: "0", color: "#4a555f" },\n'
              '        ".cm-bpGutter": { width: "14px", cursor: "pointer" },\n'
              '        ".cm-bpDot": { display: "block", width: "8px", height: "8px", margin: "6px auto 0",\n'
              '          borderRadius: "50%", background: "#e5534b" },')

s = s.replace('import \n} from', 'import\n} from')
p.write_text(s, encoding="utf-8", newline="\n")
print("RangeSetBuilder" in s, "gutter(" in s)
