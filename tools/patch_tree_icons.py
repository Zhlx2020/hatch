import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js/tree.js"
s = p.read_text(encoding="utf-8")

svg = '''const SVG = '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" '
  + 'stroke="currentColor" stroke-width="1.3" stroke-linecap="round" '
  + 'stroke-linejoin="round" aria-hidden="true">';

const CHEVRON = SVG + '<path d="M6 4l4 4-4 4"/></svg>';
const CHEVRON_DOWN = SVG + '<path d="M4 6l4 4 4-4"/></svg>';
const FOLDER = SVG + '<path d="M2 4.5A1.5 1.5 0 0 1 3.5 3h2.6c.4 0 .8.2 1 .5l.8 1h5.6A1.5 1.5 0 0 1 15 '
  + '6v6a1.5 1.5 0 0 1-1.5 1.5h-10A1.5 1.5 0 0 1 2 12z"/></svg>';
const SHEET = SVG + '<path d="M4 2.5h5l3.5 3.5V13a.5.5 0 0 1-.5.5H4a.5.5 0 0 1-.5-.5V3a.5.5 0 '
  + '0 1 .5-.5z"/><path d="M9 2.5V6h3.5"/></svg>';
const CODE = SHEET.replace("</svg>", '<path d="M6 9l-1.2 1.6L6 12.2M10 9l1.2 1.6L10 12.2"/></svg>');
const PART = SHEET.replace("</svg>", '<path d="M6 9.5h4M6 11.8h2.6"/></svg>');

function mark(row, node, open) {
  const chevron = document.createElement("span");
  chevron.className = "chev";
  const file = document.createElement("span");
  file.className = "ficon";
  if (node.kind === "dir") {
    chevron.innerHTML = open ? CHEVRON_DOWN : CHEVRON;
    file.innerHTML = FOLDER;
  } else {
    chevron.innerHTML = "";
    file.innerHTML = node.ext === ".asm" ? CODE : node.ext === ".inc" ? PART : SHEET;
  }
  row.append(chevron, file);
}
'''

s = s.replace('''const ICONS = { dir: "▸", file: "·" };

function icon(node, open) {
  if (node.kind === "dir") return open ? "▾" : "▸";
  if (node.ext === ".asm") return "▤";
  if (node.ext === ".inc") return "▦";
  return "·";
}
''', svg)

s = s.replace('''    const mark = document.createElement("span");
    mark.className = "icon";
    mark.textContent = icon(node, !collapsed.has(node.path));
    row.append(mark);
''', '''    mark(row, node, !collapsed.has(node.path));
''')
p.write_text(s, encoding="utf-8", newline="\n")

c = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/styles/layout.css"
t = c.read_text(encoding="utf-8")
t = t.replace('''#tree .row .icon {
  width: 14px;
  flex: none;
  text-align: center;
  font-size: 11px;
  color: var(--dim);
}''', '''#tree .row .chev,
#tree .row .ficon {
  flex: none;
  display: flex;
  align-items: center;
  color: var(--dim);
}
#tree .row .chev { width: 12px; justify-content: center; }
#tree .row .chev:empty { width: 12px; }''')
t = t.replace("#tree .row.dir .icon { color: var(--dir); }",
              "#tree .row.dir .ficon { color: var(--dir); }\n#tree .row.dir .chev { color: #46515e; }")
t = t.replace("#tree .row.file .icon { color: var(--dim); }",
              "#tree .row.file .ficon { color: #6a7683; }\n#tree .row:hover .chev { color: var(--dim); }")
c.write_text(t, encoding="utf-8", newline="\n")
print("ok")
