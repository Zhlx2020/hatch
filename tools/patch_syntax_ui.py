import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

# api: 带上语法
a = root / "js/api.js"
s = a.read_text(encoding="utf-8")
s = s.replace('export const disasm = (addr, count) => post("/api/disasm", { addr, count });',
              'export const disasm = (addr, count, syntax) =>\n'
              '  post("/api/disasm", { addr, count, syntax });')
a.write_text(s, encoding="utf-8", newline="\n")

# detail: 语法开关
d = root / "js/detail.js"
t = d.read_text(encoding="utf-8")
t = t.replace('let memAddr = 0;', 'let memAddr = 0;\nlet syntax = "intel";')
t = t.replace('''  const runTo = document.createElement("button");''',
'''  const bar = document.createElement("div");
  bar.className = "detail-bar";
  for (const [key, label] of [["intel", "Intel"], ["att", "AT&T"]]) {
    const button = document.createElement("button");
    button.textContent = label;
    button.className = key === syntax ? "on" : "";
    button.addEventListener("click", () => {
      syntax = key;
      renderDisasm();
    });
    bar.append(button);
  }
  wrap.append(bar);

  const runTo = document.createElement("button");''')
t = t.replace('const data = await api.disasm(hex(disAddr || eip, 8), 48);',
              'const data = await api.disasm(hex(disAddr || eip, 8), 48, syntax);')
t = t.replace('note("点圆点断点；双击行把地址挪到该处。");',
              'note(syntax === "intel"\n'
              '    ? "点圆点断点；双击行把地址挪到该处。"\n'
              '    : "AT&T 顺序是源,目的，寄存器带 %、立即数带 $。");')
d.write_text(t, encoding="utf-8", newline="\n")
print("ok")
