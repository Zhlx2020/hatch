import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

p = root / "index.html"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '<section id="files" class="pane">\n'
    '  <h2>文件 <button id="new-file" class="mini">＋</button>'
    '<button id="del-file" class="mini">－</button></h2>\n'
    '  <div class="body" id="file-list">载入中…</div>\n'
    "</section>",
    '<section id="files" class="pane">\n'
    '  <h2>文件 <button id="new-file" class="mini">＋</button>'
    '<button id="new-dir" class="mini">＋目录</button>'
    '<button id="del-file" class="mini">－</button></h2>\n'
    '  <div class="body" id="tree"></div>\n'
    '  <div id="tree-menu"></div>\n'
    "</section>",
)
p.write_text(s, encoding="utf-8", newline="\n")
print("tree" in s)
