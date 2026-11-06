// Editor entry: bundles CodeMirror 6 with a NASM mode, completion and linting.
import { autocompletion, closeBrackets, closeBracketsKeymap } from "@codemirror/autocomplete";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import {
  HighlightStyle,
  StreamLanguage,
  bracketMatching,
  indentUnit,
  syntaxHighlighting,
} from "@codemirror/language";
import { tags } from "@lezer/highlight";
import { highlightSelectionMatches, searchKeymap } from "@codemirror/search";
import { setDiagnostics } from "@codemirror/lint";
import { EditorState, Prec, StateEffect, StateField } from "@codemirror/state";
import {
  Decoration,
  EditorView,
  drawSelection,
  highlightActiveLine,
  highlightActiveLineGutter,
  keymap,
  lineNumbers,
  placeholder,
  ViewPlugin,
} from "@codemirror/view";

import REGISTERS from "./nasm_regs.js";
import { WORDS, DIRECTIVES } from "./nasm_words.js";

const LABEL = /^[A-Za-z_.$][\w.$]*:/;
const NUMBER = /^(?:0x[0-9a-fA-F]+|\d+|0b[01]+)/;
const IDENT = /^[A-Za-z_.$][\w.$]*/;

function token(stream) {
  if (stream.eatSpace()) return null;
  if (stream.match(";") || stream.match("//")) {
    stream.skipToEnd();
    return "comment";
  }
  if (stream.match(/^"[^"]*"?/) || stream.match(/^'[^']*'?/)) return "string";
  if (stream.match(LABEL)) return "labelName";
  if (stream.match(/^%[A-Za-z]+/)) return "keyword";
  if (stream.match(NUMBER)) return "number";
  const word = stream.match(IDENT);
  if (word) {
    const text = word[0].toLowerCase();
    if (DIRECTIVES.has(text) || WORDS.has(text)) return "keyword";
    if (REGISTERS.has(text)) return "typeName";
    return "variableName";
  }
  if (stream.match(/^[[\](){}:,.+\-*/&|^~<>!=]+/)) return "operator";
  stream.next();
  return null;
}

const nasm = StreamLanguage.define({ name: "nasm", token });

const theme = EditorView.theme(
  {
    "&": { height: "100%", fontSize: "12.5px", background: "transparent" },
    ".cm-scroller": {
      fontFamily: '"Cascadia Mono", Consolas, "Microsoft YaHei", monospace',
      lineHeight: "1.55",
    },
    ".cm-content": { caretColor: "#5fbf92" },
    ".cm-gutters": { background: "transparent", border: "0", color: "#4a555f" },
    ".cm-activeLine": { background: "#ffffff06" },
    ".cm-execLine": { background: "#5fbf9218", boxShadow: "inset 2px 0 0 #5fbf92" },
    ".cm-activeLineGutter": { color: "#5fbf92", background: "transparent" },
    "&.cm-focused": { outline: "none" },
    ".cm-selectionBackground, ::selection": { background: "#2a3a46" },
    ".cm-tooltip": {
      background: "#141a20",
      border: "1px solid #1e262e",
      color: "#c6d0d8",
    },
    ".cm-tooltip-autocomplete ul li[aria-selected]": { background: "#1e262e", color: "#5fbf92" },
    ".cm-diagnostic": { borderLeft: "3px solid #d2686b", paddingLeft: "8px" },
    ".cm-lintRange-error": { textDecoration: "underline wavy #d2686b" },
  },
  { dark: true },
);

const highlight = syntaxHighlighting(
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
);

const setExec = StateEffect.define();

const execField = StateField.define({
  create: () => 0,
  update(value, tr) {
    for (const effect of tr.effects) {
      if (effect.is(setExec)) value = effect.value;
    }
    return value;
  },
});

const execDecor = Decoration.line({ class: "cm-execLine" });

const execPlugin = ViewPlugin.fromClass(
  class {
    constructor(view) {
      this.decorations = this.build(view);
    }
    update(update) {
      if (update.docChanged || update.viewportChanged || update.transactions
        || update.state.field(execField) !== update.startState.field(execField)) {
        this.decorations = this.build(update.view);
      }
    }
    build(view) {
      const line = view.state.field(execField);
      if (!line) return Decoration.none;
      try {
        return Decoration.set([execDecor.range(view.state.doc.line(line).from)]);
      } catch {
        return Decoration.none;
      }
    }
  },
  { decorations: (value) => value.decorations },
);

function words() {
  return [...WORDS, ...REGISTERS, ...DIRECTIVES].map((label) => ({
    label,
    type: "keyword",
  }));
}

function labels(state) {
  const seen = new Set();
  const out = [];
  for (let n = 1; n <= state.doc.lines; n += 1) {
    const text = state.doc.line(n).text;
    const match = /^([A-Za-z_.$][\w.$]*):/.exec(text);
    if (match && !seen.has(match[1])) {
      seen.add(match[1]);
      out.push({ label: match[1], type: "variable" });
    }
    const decl = /^\s*([A-Za-z_.$][\w.$]*)\s+(?:equ|db|dw|dd|dq)\b/i.exec(text);
    if (decl && !seen.has(decl[1])) {
      seen.add(decl[1]);
      out.push({ label: decl[1], type: "variable" });
    }
  }
  return out;
}

function nasmCompletions(context) {
  const word = context.matchBefore(/[A-Za-z_.$%][\w.$]*/);
  if (!word) return null;
  if (word.from === word.to && !context.explicit) return null;
  return { from: word.from, options: [...words(), ...labels(context.state)] };
}

export function create(parent, { onSave, onChange } = {}) {
  const state = EditorState.create({
    doc: "",
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      highlightActiveLine(),
      drawSelection(),
      bracketMatching(),
      closeBrackets(),
      history(),
      autocompletion({ override: [nasmCompletions], icons: false, maxRenderedOptions: 20 }),
      highlightSelectionMatches(),
      nasm,
      theme,
      highlight,
      execField,
      execPlugin,
      EditorState.tabSize.of(8),
      indentUnit.of("    "),
      placeholder("这里是你的引导扇区…"),
      Prec.highest(
        keymap.of([
          {
            key: "Mod-s",
            preventDefault: true,
            run: () => {
              if (onSave) onSave(false);
              return true;
            },
          },
          {
            key: "Mod-Enter",
            preventDefault: true,
            run: () => {
              if (onSave) onSave(true);
              return true;
            },
          },
          indentWithTab,
          ...closeBracketsKeymap,
          ...defaultKeymap,
          ...searchKeymap,
          ...historyKeymap,
        ]),
      ),
      EditorView.updateListener.of((update) => {
        if (update.docChanged && onChange) onChange();
      }),
    ],
  });

  const view = new EditorView({ state, parent });

  return {
    getValue: () => view.state.doc.toString(),
    setValue(text) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: text },
        selection: { anchor: 0 },
      });
    },
    focus: () => view.focus(),
    markLine(line) {
      view.dispatch({ effects: setExec.of(line || 0) });
    },
    scrollTo(line) {
      try {
        const info = view.state.doc.line(Math.min(line, view.state.doc.lines));
        view.dispatch({ effects: EditorView.scrollIntoView(info.from, { y: "center" }) });
      } catch {
        /* 行号超出范围时不动 */
      }
    },
    setDiagnostics(list) {
      const items = [];
      for (const item of list || []) {
        const line = Math.min(Math.max(item.line || 1, 1), view.state.doc.lines);
        const info = view.state.doc.line(line);
        items.push({
          from: info.from,
          to: Math.max(info.to, info.from + 1),
          severity: item.severity || "error",
          message: item.message,
        });
      }
      view.dispatch(setDiagnostics(view.state, items));
    },
  };
}
