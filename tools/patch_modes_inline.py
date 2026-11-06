import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

d = root / "assets/ui/js/detail.js"
s = d.read_text(encoding="utf-8")
s = s.replace('''  const bar = document.createElement("div");
  bar.className = "detail-bar";
  for (const [key, label] of [["intel", "Intel"], ["att", "AT&T"]]) {
    const button = document.createElement("button");
    button.textContent = label;
    button.className = key === syntax ? "on" : "";
    button.addEventListener("click", () => {
      syntax = key;
      renderDisasm();
    });
    bar.append(button);
  }
  wrap.append(bar);
''',
'''  const modes = document.createElement("span");
  modes.className = "modes";
  for (const [key, label] of [["intel", "Intel"], ["att", "AT&T"]]) {
    const button = document.createElement("button");
    button.textContent = label;
    button.className = key === syntax ? "on" : "";
    button.addEventListener("click", () => {
      syntax = key;
      renderDisasm();
    });
    modes.append(button);
  }
  wrap.append(modes);
''')
d.write_text(s, encoding="utf-8", newline="\n")

c = root / "assets/ui/styles/detail.css"
t = c.read_text(encoding="utf-8")
t = t.replace("#detail-body .detail-bar button.on { border-color: var(--accent); color: var(--accent); }",
"""#detail-body .modes { display: flex; gap: 4px; margin-left: 4px; }
#detail-body .modes button.on { border-color: var(--accent); color: var(--accent); }""")
c.write_text(t, encoding="utf-8", newline="\n")
print("ok")
