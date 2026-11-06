import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js/editor.js"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'const listEl = document.getElementById("chapter-list");',
    'const listEl = document.getElementById("chapter-list");\nconst noteEl = document.getElementById("note");',
)
s = s.replace(
    '  label(chapter.title);',
    '  noteEl.textContent = chapter.note || "";\n  label(chapter.title);',
)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")

