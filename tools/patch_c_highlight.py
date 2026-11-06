import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tools/editor_entry.js"
s = p.read_text(encoding="utf-8")

old_token = s[s.index("// C：注释、字符串、字符、预处理、数字、关键字/类型分开上色"):s.index('const clike = StreamLanguage.define({ name: "c", token: cToken });')]

new_token = '''// C：注释、字符串、字符、预处理、数字、关键字/类型分开上色。
// 预处理要拆开看：指令本身一种颜色，被包含的头文件名另一种；
// 函数名单独一类，不然满屏都是变量色，看不出哪儿在调用。
const C_NUMBER = /^(?:0[xX][0-9a-fA-F]+|\\d+\\.?\\d*(?:[eE][-+]?\\d+)?)[uUlLfF]*/;
const C_WORD = /^[A-Za-z_]\\w*/;
const C_DIRECTIVE = /^\\s*#\\s*([A-Za-z_]+)/;
const C_HEADER = /^(?:<[^>\\n]*>|"[^"\\n]*")/;

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
  if (stream.match(/^"(?:[^"\\\\]|\\\\.)*"?/)) return "string";
  if (stream.match(/^'(?:[^'\\\\]|\\\\.)*'?/)) return "string";
  const directive = stream.sol() && stream.match(C_DIRECTIVE);
  if (directive) {
    state.inHeader = /include/.test(directive[1]);
    return "meta";
  }
  if (stream.match(C_NUMBER)) return "number";
  const word = stream.match(C_WORD);
  if (word) {
    const text = word[0];
    if (KEYWORDS.includes(text)) return "keyword";
    if (stream.match(/^\\s*\\(/, false)) return "variableName.function";
    if (TYPES.includes(text)) return "typeName";
    if (LIBRARY.includes(text)) return "variableName.function";
    return "variableName";
  }
  if (stream.match(/^[{}()\\[\\];,.+\\-*/%&|^~!<>=?:]+/)) return "operator";
  stream.next();
  return null;
}

'''

s = s.replace(old_token, new_token)
s = s.replace(
    'const clike = StreamLanguage.define({ name: "c", token: cToken });',
    'const clike = StreamLanguage.define({\n'
    '  name: "c",\n'
    '  startState: () => ({ inHeader: false }),\n'
    '  token: cToken,\n'
    '});')

# 主题：函数、预处理指令、头文件名各给一个颜色
s = s.replace('''    { tag: tags.labelName, color: "#d8b573" },''',
'''    { tag: tags.labelName, color: "#d8b573" },
    { tag: tags.meta, color: "#c98fd6" },
    { tag: tags.string.special, color: "#d9a06f" },
    { tag: [tags.function(tags.variableName), tags.function(tags.propertyName)],
      color: "#7fc5e0" },''')

p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
