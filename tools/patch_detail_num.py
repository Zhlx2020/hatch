import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js/detail.js"
s = p.read_text(encoding="utf-8")

s = s.replace('const hex = (value, digits) => value.toString(16).padStart(digits, "0");',
              'const hex = (value, digits) => value.toString(16).padStart(digits, "0");\n'
              'const num = (value) => (typeof value === "number"\n'
              '  ? value\n'
              '  : parseInt(String(value || "0").replace(/^0x/i, ""), 16) || 0);')

s = s.replace('''    memAddr = parseInt(regs[name] || "0", 16);''', '''    memAddr = num(regs[name]);''')
s = s.replace('''  const data = await api.mem(hex(memAddr, 8), 256);''',
              '''  if (!memAddr) memAddr = num(regs.eip);
  const data = await api.mem(hex(memAddr, 8), 256);''')
s = s.replace('''  const eip = parseInt(regs.eip || "0", 16);''', '''  const eip = num(regs.eip);''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
