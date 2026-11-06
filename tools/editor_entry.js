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
import {
  Compartment,
  EditorState,
  Prec,
  RangeSet,
  RangeSetBuilder,
  StateEffect,
  StateField,
} from "@codemirror/state";
import {
  Decoration,
  EditorView,
  drawSelection,
  highlightActiveLine,
  highlightActiveLineGutter,
  gutter,
  GutterMarker,
  keymap,
  lineNumbers,
  placeholder,
  ViewPlugin,
} from "@codemirror/view";

import REGISTERS from "./nasm_regs.js";
import { KEYWORDS, LIBRARY, PREPROCESSOR, TYPES, documentWords } from "./clike.js";
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

// C：注释、字符串、字符、预处理、数字、关键字/类型分开上色。
// 预处理要拆开看：指令本身一种颜色，被包含的头文件名另一种；
// 函数名单独一类，不然满屏都是变量色，看不出哪儿在调用。
const C_NUMBER = /^(?:0[xX][0-9a-fA-F]+|\d+\.?\d*(?:[eE][-+]?\d+)?)[uUlLfF]*/;
const C_WORD = /^[A-Za-z_]\w*/;
const C_DIRECTIVE = /^\s*#\s*([A-Za-z_]+)/;
const C_HEADER = /^(?:<[^>\n]*>|"[^"\n]*")/;

function cToken(stream, state) {
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
  if (state.inHeader) {
    state.inHeader = false;
    if (stream.match(C_HEADER)) return "string.special";
  }
  if (stream.match(/^"(?:[^"\\]|\\.)*"?/)) return "string";
  if (stream.match(/^'(?:[^'\\]|\\.)*'?/)) return "string";
  // 缩进过的 #define 也算指令：看行首到现在是不是只剩空白
  const atLineStart = /^\s*$/.test(stream.string.slice(0, stream.start));
  const directive = atLineStart && stream.match(C_DIRECTIVE);
  if (directive) {
    state.inHeader = /include/.test(directive[1]);
    return "meta";
  }
  if (stream.match(C_NUMBER)) return "number";
  const word = stream.match(C_WORD);
  if (word) {
    const text = word[0];
    if (KEYWORDS.includes(text)) return "keyword";
    if (stream.match(/^\s*\(/, false)) return "variableName.function";
    if (TYPES.includes(text)) return "typeName";
    if (LIBRARY.includes(text)) return "variableName.function";
    return "variableName";
  }
  if (stream.match(/^[{}()\[\];,.+\-*/%&|^~!<>=?:]+/)) return "operator";
  stream.next();
  return null;
}

const clike = StreamLanguage.define({
  name: "c",
  startState: () => ({ inHeader: false }),
  token: cToken,
});

const theme = EditorView.theme(
  {
    "&": { height: "100%", fontSize: "12.5px", background: "transparent" },
    ".cm-scroller": {
      fontFamily: '"Cascadia Mono", Consolas, "Microsoft YaHei", monospace',
      lineHeight: "1.55",
    },
    ".cm-content": { caretColor: "#5fbf92" },
    ".cm-gutters": { background: "transparent", border: "0", color: "#4a555f" },
        ".cm-bpGutter": { width: "14px", cursor: "pointer" },
        ".cm-bpDot": { display: "block", width: "8px", height: "8px", margin: "6px auto 0",
          borderRadius: "50%", background: "#e5534b" },
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
    { tag: tags.meta, color: "#c98fd6" },
    { tag: tags.special(tags.string), color: "#d9a06f" },
    { tag: [tags.function(tags.variableName), tags.function(tags.propertyName)],
      color: "#7fc5e0" },
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

// 行断点：字段存行号，gutter 画红点，点击交给面板去解析地址
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
const bpBlank = new (class extends GutterMarker {})();

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
    // 每一行都给一个标记：没有断点的用空标记，gutter 才会为整屏建出可点行
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
    }
  },
  { markers: (value) => value.markers },
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

const C_KEYWORD_OPTIONS = [...KEYWORDS, ...TYPES, ...LIBRARY, ...PREPROCESSOR];

function cCompletions(context) {
  const word = context.matchBefore(/[#A-Za-z_]\w*/);
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

function nasmCompletions(context) {
  const word = context.matchBefore(/[A-Za-z_.$%][\w.$]*/);
  if (!word) return null;
  if (word.from === word.to && !context.explicit) return null;
  return { from: word.from, options: [...words(), ...labels(context.state)] };
}

function langSupport(kind) {
  return [
    kind === "c" ? clike : nasm,
    autocompletion({
      override: [kind === "c" ? cCompletions : nasmCompletions],
      icons: false,
      maxRenderedOptions: 20,
    }),
  ];
}

export function create(parent, { onSave, onChange, onToggleLine } = {}) {
  const langBox = new Compartment();
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
      langBox.of(langSupport("asm")),
      highlightSelectionMatches(),
      nasm,
      theme,
      highlight,
      execField,
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
      }),
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
    setLanguage(kind) {
      view.dispatch({ effects: langBox.reconfigure(langSupport(kind)) });
    },
    markLine(line) {
      view.dispatch({ effects: setExec.of(line || 0) });
    },
    breakpoints() {
      return [...view.state.field(bpLines)];
    },
    setBreakpoints(lines) {
      view.dispatch({ effects: setBps.of([...(lines || [])]) });
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
