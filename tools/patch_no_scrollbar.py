import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/styles"

b = root / "base.css"
s = b.read_text(encoding="utf-8")
if "scrollbar-width: none" not in s:
    s = s.replace("* {", """*::-webkit-scrollbar { width: 0; height: 0; }
* { scrollbar-width: none; }

* {""", 1)
    if "scrollbar-width: none" not in s:
        s = "*::-webkit-scrollbar { width: 0; height: 0; }\nhtml, body, * { scrollbar-width: none; }\n\n" + s
b.write_text(s, encoding="utf-8", newline="\n")

# asm 图标稍亮一点
l = root / "layout.css"
t = l.read_text(encoding="utf-8")
t = t.replace("#tree .row.file .ficon { color: #6a7683; }",
              "#tree .row.file .ficon { color: #6a7683; }\n#tree .row.file.asm .ficon { color: #8b98a6; }")
l.write_text(t, encoding="utf-8", newline="\n")
print("ok")
