import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/styles/detail.css"
s = p.read_text(encoding="utf-8")
s += """
#settings {
  position: fixed;
  top: 12vh;
  left: 50%;
  transform: translateX(-50%);
  width: 520px;
  max-height: 70vh;
  box-sizing: border-box;
  z-index: 70;
  display: none;
  flex-direction: column;
  padding: 10px;
  background: var(--panel);
  border: 1px solid var(--edge);
  border-radius: 6px;
  box-shadow: 0 18px 40px #0009;
}
#settings.open { display: flex; }
#settings-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--edge);
}
#settings-tabs .grow,
#settings-foot .grow { flex: 1; }
#settings-tabs button { padding: 5px 12px; font-size: 13.5px; }
#settings-tabs button.on { border-color: var(--accent); color: var(--accent); }
#settings-body { padding: 12px 2px; overflow: auto; }
#settings-body label { display: block; margin-bottom: 12px; font-size: 14px; color: var(--dim); }
#settings-body label span { display: block; margin-bottom: 4px; }
#settings-body input[type="text"],
#settings-body input[type="number"],
#settings-body textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 6px 8px;
  font: inherit;
  font-size: 14px;
  color: var(--text);
  background: var(--ink);
  border: 1px solid var(--edge);
  border-radius: 4px;
}
#settings-body textarea { height: 74px; resize: vertical; }
#settings-body .hint { color: var(--dim); font-size: 12.5px; margin-top: 4px; }
#settings-body .check { display: flex; align-items: center; gap: 8px; }
#settings-body .check input { width: auto; }
#settings-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--edge);
}
#settings-note { font-size: 12.5px; color: var(--dim); }
#settings-note.bad { color: #e5534b; }
"""
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
