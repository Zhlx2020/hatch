// C 词的来源：关键字/类型/标准库名 + 文档里出现的标识符。
export const KEYWORDS = [
  "if", "else", "for", "while", "do", "switch", "case", "default", "break",
  "continue", "return", "goto", "sizeof", "typedef", "struct", "union", "enum",
  "static", "extern", "const", "volatile", "register", "inline", "restrict",
  "_Static_assert", "_Alignof", "_Alignas", "asm",
];

export const TYPES = [
  "void", "char", "short", "int", "long", "float", "double", "signed",
  "unsigned", "_Bool", "size_t", "ssize_t", "uint8_t", "uint16_t", "uint32_t",
  "uint64_t", "int8_t", "int16_t", "int32_t", "int64_t", "bool", "uintptr_t",
  "intptr_t", "ptrdiff_t",
];

export const LIBRARY = [
  "memcpy", "memset", "memmove", "memcmp", "strlen", "strcpy", "strncpy",
  "strcmp", "strncmp", "printf", "sprintf", "snprintf", "puts", "putchar",
  "malloc", "calloc", "realloc", "free", "abort", "assert",
];

export const PREPROCESSOR = [
  "#include", "#define", "#undef", "#ifdef", "#ifndef", "#endif", "#else",
  "#elif", "#pragma",
];

export function documentWords(text) {
  const seen = new Set();
  const out = [];
  const re = /\b[A-Za-z_]\w{1,40}\b/g;
  let match = re.exec(text);
  while (match && out.length < 400) {
    const word = match[0];
    if (!seen.has(word)) {
      seen.add(word);
      out.push(word);
    }
    match = re.exec(text);
  }
  return out;
}
