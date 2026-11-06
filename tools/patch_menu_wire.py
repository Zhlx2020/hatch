import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

c = root / "src/oslab/assets/ui/styles/detail.css"
s = c.read_text(encoding="utf-8")
s += """
#run-group {
  position: relative;
  display: flex;
  align-items: stretch;
  gap: 1px;
}
#run-more {
  padding: 0 6px;
  font-size: 11px;
  border-radius: 0 3px 3px 0;
}
#run-group #run { border-radius: 3px 0 0 3px; }
#run-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  z-index: 80;
  display: none;
  flex-direction: column;
  min-width: 168px;
  padding: 4px;
  background: var(--panel);
  border: 1px solid var(--edge);
  border-radius: 4px;
  box-shadow: 0 14px 30px #0008;
}
#run-menu.open { display: flex; }
#run-menu button {
  text-align: left;
  padding: 6px 9px;
  border-radius: 3px;
  background: transparent;
  border: 0;
}
#run-menu button:hover { background: var(--edge); }
"""
c.write_text(s, encoding="utf-8", newline="\n")

b = root / "src/oslab/assets/ui/js/boot.js"
t = b.read_text(encoding="utf-8")
t = t.replace('''document.getElementById("run").addEventListener("click", boot);''',
'''document.getElementById("run").addEventListener("click", () => runAction("main"));
document.getElementById("run-more").addEventListener("click", (ev) => {
  ev.stopPropagation();
  document.getElementById("run-menu").classList.toggle("open");
});
document.getElementById("run-menu").addEventListener("click", (ev) => {
  const item = ev.target.closest("button[data-act]");
  if (item) runAction(item.dataset.act);
});
document.addEventListener("click", () => {
  document.getElementById("run-menu").classList.remove("open");
});''')
b.write_text(t, encoding="utf-8", newline="\n")
print("ok")
