import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

# 目录用蓝色，文件名保持中性，靠后缀区分
b = root / "styles/base.css"
s = b.read_text(encoding="utf-8")
if "--dir:" not in s:
    s = s.replace("--accent: #5fbf92;", "--accent: #5fbf92;\n  --dir: #63a6e8;")
b.write_text(s, encoding="utf-8", newline="\n")

l = root / "styles/layout.css"
t = l.read_text(encoding="utf-8")
t = t.replace("#tree .row.dir .icon { color: var(--accent); }",
              "#tree .row.dir .icon { color: var(--dir); }")
t = t.replace("#tree .row.dir .label { color: var(--text); font-weight: 600; letter-spacing: .02em; }",
              "#tree .row.dir .label { color: var(--dir); font-weight: 600; letter-spacing: .02em; }")
t = t.replace("#tree .row.file .label { color: var(--dim); }",
              "#tree .row.file .label { color: var(--text); }")
t = t.replace("#tree .row.file.asm .label { color: var(--text); }", "")
t = t.replace("#tree .row.file .ext { color: var(--dim); font-size: 10px; letter-spacing: .06em; }",
              "#tree .row.file .ext { color: var(--dim); font-size: 11px; letter-spacing: .04em; }")
l.write_text(t, encoding="utf-8", newline="\n")

# 名称与后缀分开渲染
j = root / "js/tree.js"
u = j.read_text(encoding="utf-8")
u = u.replace('''    const label = document.createElement("span");
    label.className = "label";
    label.textContent = node.name;
    row.append(label);''',
'''    const label = document.createElement("span");
    label.className = "label";
    if (node.kind === "file" && node.ext) {
      label.textContent = node.name.slice(0, -node.ext.length);
      const ext = document.createElement("span");
      ext.className = "ext";
      ext.textContent = node.ext;
      label.append(ext);
    } else {
      label.textContent = node.name;
    }
    row.append(label);''')
j.write_text(u, encoding="utf-8", newline="\n")
print("ok")
