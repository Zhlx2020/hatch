import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tools/editor_entry.js"
s = p.read_text(encoding="utf-8")

s = s.replace(
    'import { StreamLanguage, bracketMatching, indentUnit } from "@codemirror/language";',
    'import {\n  HighlightStyle,\n  StreamLanguage,\n  bracketMatching,\n  indentUnit,\n  syntaxHighlighting,\n} from "@codemirror/language";\nimport { tags } from "@lezer/highlight";',
)

s = s.replace('''const highlight = EditorView.baseTheme({
  ".cm-labelName": { color: "#d8b573" },
  ".cm-keyword": { color: "#c98fd6" },
  ".cm-typeName": { color: "#6fb2d2" },
  ".cm-number": { color: "#8fc98f" },
  ".cm-string": { color: "#d99b6f" },
  ".cm-comment": { color: "#5c6a73", fontStyle: "italic" },
  ".cm-variableName": { color: "#c9d3da" },
});''',
'''const highlight = syntaxHighlighting(
  HighlightStyle.define([
    { tag: tags.labelName, color: "#d8b573" },
    { tag: tags.keyword, color: "#c98fd6" },
    { tag: tags.typeName, color: "#6fb2d2" },
    { tag: tags.number, color: "#8fc98f" },
    { tag: tags.string, color: "#d99b6f" },
    { tag: [tags.comment, tags.lineComment], color: "#5c6a73", fontStyle: "italic" },
    { tag: tags.variableName, color: "#c9d3da" },
    { tag: tags.operator, color: "#9aa7b3" },
  ]),
);''',
)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
