import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/styles/layout.css"
s = p.read_text(encoding="utf-8")

old = """#files .body { padding: 6px; }
.file {
  display: block;
  width: 100%;
  text-align: left;
  padding: 5px 8px;
  margin-bottom: 3px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 3px;
}
.file:hover { border-color: var(--edge); }
.file.active { border-color: var(--accent); color: var(--accent); }
"""

new = """#files .body { padding: 6px 4px; user-select: none; }
#tree .row {
  display: flex;
  align-items: center;
  gap: 5px;
  height: 22px;
  padding-right: 6px;
  border: 1px solid transparent;
  border-radius: 3px;
  white-space: nowrap;
  overflow: hidden;
}
#tree .row .icon { width: 11px; color: var(--dim); flex: none; text-align: center; }
#tree .row .label { overflow: hidden; text-overflow: ellipsis; }
#tree .row:hover { background: color-mix(in srgb, var(--edge) 40%, transparent); }
#tree .row.active { border-color: var(--accent); color: var(--accent); }
#tree .row.dir .label { color: var(--fg); font-weight: 600; letter-spacing: .02em; }
#tree .row.drop { border-color: var(--accent); border-style: dashed; }
#tree .row.dragging { opacity: .5; }

#tree-menu {
  position: fixed;
  z-index: 40;
  display: none;
  flex-direction: column;
  min-width: 132px;
  padding: 4px;
  background: var(--panel);
  border: 1px solid var(--edge);
  border-radius: 4px;
  box-shadow: 0 8px 24px #0008;
}
#tree-menu.open { display: flex; }
#tree-menu button {
  text-align: left;
  padding: 5px 8px;
  background: transparent;
  border: 0;
  border-radius: 3px;
}
#tree-menu button:hover { background: var(--edge); }
"""

assert old in s
p.write_text(s.replace(old, new), encoding="utf-8", newline="\n")
print("ok")
