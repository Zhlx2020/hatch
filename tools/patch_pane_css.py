import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/styles"

# 标题不参与收缩，永远可见
b = root / "base.css"
s = b.read_text(encoding="utf-8")
s = s.replace(".pane > h2 {\n  margin: 0;", ".pane > h2 {\n  flex: none;\n  margin: 0;")
s = s.replace(".pane > h2 { display: flex; align-items: center; gap: 4px; }",
              ".pane > h2 { display: flex; align-items: center; gap: 6px; }\n"
              ".pane > h2 .tag { color: var(--edge); }\n"
              ".pane > h2 .tag:not(:empty) { color: var(--dim); }")
s = s.replace("#regs { flex: 1; }", "#regs { flex: none; }")
b.write_text(s, encoding="utf-8", newline="\n")

# 窄窗口：编辑器在上面一行，屏幕与面板放到下面一行
l = root / "layout.css"
t = l.read_text(encoding="utf-8")
t += """
@media (max-width: 1120px) {
  body {
    grid-template-columns: 210px minmax(0, 1fr);
    grid-template-rows: 42px minmax(0, 1fr) 40vh;
  }
  #files { grid-area: 2 / 1; }
  #editor { grid-area: 2 / 2; }
  aside {
    grid-area: 3 / 1 / 4 / 3;
    flex-direction: row;
    border-top: 1px solid var(--edge);
  }
  #screenwrap { flex: 1 1 auto; min-width: 0; }
  #panels { flex: 0 0 46%; min-width: 300px; }
}
"""
l.write_text(t + "\n", encoding="utf-8", newline="\n")

# 面板内部的排布与配色
p = root / "panels.css"
u = p.read_text(encoding="utf-8")
u += """
/* 小面板：结构化显示 ------------------------------------------------ */
#panels .body { padding: 6px 8px; font: 12px/1.7 ui-monospace, Consolas, monospace; }
#panels .empty { color: var(--dim); }

#regs.rgrid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px 10px;
}
#regs .rcell {
  display: flex;
  gap: 6px;
  padding: 0 4px;
  border-left: 2px solid transparent;
  white-space: nowrap;
  overflow: hidden;
}
#regs .rcell.here { border-left-color: var(--accent); background: #5fbf921a; }
#regs .rn { color: var(--dim); width: 30px; flex: none; }
#regs .rv { color: var(--text); font-variant-numeric: tabular-nums; }
#regs .rv.zero { color: #4d5763; }
#regs .rflags { display: flex; gap: 3px; margin-top: 5px; grid-column: 1 / -1; }
#regs .fl {
  padding: 0 4px;
  border: 1px solid var(--edge);
  border-radius: 2px;
  font-size: 10px;
  color: #4d5763;
}
#regs .fl.on { color: #0b0d10; background: var(--accent); border-color: var(--accent); }
#regs .fl.raw { border: 0; color: var(--dim); }
#regs .rsegs { display: flex; gap: 8px; margin-top: 4px; color: #55606c; font-size: 11px; }

#bps { display: flex; flex-wrap: wrap; gap: 4px; padding: 6px 8px 0; font-size: 11px; }
#bps .bp { padding: 0 4px; border: 1px solid var(--danger); border-radius: 2px; color: var(--danger); }

#disasm .drow {
  display: flex;
  gap: 8px;
  padding: 0 4px;
  border-left: 2px solid transparent;
  white-space: pre;
  overflow: hidden;
}
#disasm .drow.here { border-left-color: var(--accent); background: #5fbf921a; }
#disasm .dot {
  width: 8px;
  height: 8px;
  margin-top: 6px;
  flex: none;
  border-radius: 50%;
  border: 1px solid var(--edge);
}
#disasm .dot.on { background: var(--danger); border-color: var(--danger); }
#disasm .addr { color: #55606c; }
#disasm .bytes { color: #3f4954; width: 132px; flex: none; overflow: hidden; }
#disasm .op { color: var(--text); }

#mem .mrow { display: flex; gap: 10px; white-space: pre; }
#mem .addr { color: #55606c; }
#mem .hex { display: flex; gap: 3px; }
#mem .byte { color: var(--text); }
#mem .byte.zero { color: #39424d; }
#mem .asis { color: #55606c; }
"""
p.write_text(u, encoding="utf-8", newline="\n")
print("ok")
