import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "tests/unit"

p = root / "test_disasm_syntax.py"
s = p.read_text(encoding="utf-8")
s = s.replace('assert "xor    eax,eax" in text', 'assert "xor    ax,ax" in text')
s = s.replace('assert "%eax" not in text', 'assert "%ax" not in text')
s = s.replace('assert "xor    %eax,%eax" in text', 'assert "xor    %ax,%ax" in text')
s = s.replace('assert any("%eax" in line for line in disasm.load(image))',
              'assert any("%ax" in line for line in disasm.load(image))')
s = s.replace('"""Disassembly keeps both syntaxes; Intel is the default."""',
              '"""Disassembly keeps both syntaxes, decodes as 16 bit, Intel by default."""')
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "test_disasm.py"
t = q.read_text(encoding="utf-8")
t = t.replace('assert "%eax" in text', 'assert "%ax" in text')
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
