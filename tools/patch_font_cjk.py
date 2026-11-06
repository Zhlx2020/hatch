import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

stack = '"Cascadia Mono", Consolas, "Microsoft YaHei", monospace'

b = root / "styles/base.css"
s = b.read_text(encoding="utf-8")
s = s.replace('font: 12px/1.5 "Cascadia Mono", Consolas, monospace;',
              'font: 12px/1.5 %s;' % stack)
b.write_text(s, encoding="utf-8", newline="\n")

d = root / "styles/detail.css"
t = d.read_text(encoding="utf-8")
t = t.replace("font: 12px/1.5 ui-monospace, Consolas, monospace;", "font: 12px/1.5 %s;" % stack)
d.write_text(t, encoding="utf-8", newline="\n")
print("ok")
