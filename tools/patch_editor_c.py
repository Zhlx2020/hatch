import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tools/editor_entry.js"
s = p.read_text(encoding="utf-8")

s = s.replace('''import REGISTERS from "./nasm_regs.js";''',
'''import REGISTERS from "./nasm_regs.js";
import { KEYWORDS, LIBRARY, PREPROCESSOR, TYPES, documentWords } from "./clike.js";''')

s = s.replace('''const nasm = StreamLanguage.define({ name: "nasm", token });''',
'''const nasm = StreamLanguage.define({ name: "nasm", token });

// C：注释、字符串、字符、预处理、数字、关键字/类型分开上色
const C_NUMBER = /^(?:0[xX][0-9a-fA-F]+|\\d+\\.?\\d*(?:[eE][-+]?\\d+)?)[uUlLfF]*/;
const C_WORD = /^[A-Za-z_]\\w*/;

function cToken(stream) {
  if (stream.eatSpace()) return null;
  if (stream.match("//")) {
    stream.skipToEnd();
    return "comment";
  }
  if (stream.match("/*")) {
    while (!stream.eol()) {
      if (stream.match("*/")) break;
      stream.next();
    }
    return "comment";
  }
  if (stream.match(/^"(?:[^"\\\\]|\\\\.)*"?/)) return "string";
  if (stream.match(/^'(?:[^'\\\\]|\\\\.)*'?/)) return "string";
  if (stream.sol() && stream.match(/^\\s*#[A-Za-z]+/)) return "meta";
  if (stream.match(C_NUMBER)) return "number";
  const word = stream.match(C_WORD);
  if (word) {
    const text = word[0];
    if (KEYWORDS.includes(text)) return "keyword";
    if (TYPES.includes(text)) return "typeName";
    if (LIBRARY.includes(text)) return "typeName";
    return "variableName";
  }
  if (stream.match(/^[{}()\\[\\];,.+\\-*/%&|^~!<>=?:]+/)) return "operator";
  stream.next();
  return null;
}

const clike = StreamLanguage.define({ name: "c", token: cToken });''')

s = s.replace('''function nasmCompletions(context) {''',
'''const C_KEYWORD_OPTIONS = [...KEYWORDS, ...TYPES, ...LIBRARY, ...PREPROCESSOR];

function cCompletions(context) {
  const word = context.matchBefore(/[#A-Za-z_]\\w*/);
  if (!word) return null;
  if (word.from === word.to && !context.explicit) return null;
  const near = context.state.doc.toString();
  return {
    from: word.from,
    options: [
      ...C_KEYWORD_OPTIONS.map((label) => ({ label, type: "keyword" })),
      ...documentWords(near)
        .filter((label) => label.startsWith(word.text) && label !== word.text)
        .slice(0, 60)
        .map((label) => ({ label, type: "variable" })),
    ],
  };
}

function nasmCompletions(context) {''')

s = s.replace('''      autocompletion({ override: [nasmCompletions], icons: false, maxRenderedOptions: 20 }),''',
'''      langBox.of(langFacet.of("asm")),''')

s = s.replace('''export function create(parent, { onSave, onChange, onToggleLine } = {}) {''',
'''const langFacet = { of: (value) => value };

export function create(parent, { onSave, onChange, onToggleLine } = {}) {
  const langBox = new Compartment();''')

s = s.replace('''import { EditorState, Prec, RangeSet, RangeSetBuilder, StateEffect, StateField } from "@codemirror/state";''',
'''import {
  Compartment,
  EditorState,
  Prec,
  RangeSet,
  RangeSetBuilder,
  StateEffect,
  StateField,
} from "@codemirror/state";''')

p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
