import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

l = root / "styles/layout.css"
s = l.read_text(encoding="utf-8")
s = s.replace("""aside {
  display: grid;
  grid-template-rows: minmax(0, 1fr) 292px;
  gap: 1px;
  min-height: 0;
}

#panels {
  display: grid;""",
"""aside {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-height: 0;
}

#panels {
  flex: 1 1 auto;
  display: grid;""")
l.write_text(s, encoding="utf-8", newline="\n")

p = root / "styles/panels.css"
t = p.read_text(encoding="utf-8")
t = t.replace("""#screenwrap {
  display: grid;
  place-items: center;
  padding: 8px;
  min-width: 0;
  min-height: 0;
}

#screen {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  background: #000;
  display: block;""",
"""#screenwrap {
  flex: 0 1 auto;
  width: 100%;
  max-height: 100%;
  aspect-ratio: 720 / 478;
  min-height: 0;
  padding: 8px;
  box-sizing: border-box;
  display: grid;
}

#screen {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
  display: block;""")
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
