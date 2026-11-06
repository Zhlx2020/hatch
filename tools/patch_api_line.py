import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js/api.js"
s = p.read_text(encoding="utf-8")
if "export const line" not in s:
    s += '''
export const line = (path, row) =>
  get("/api/line?path=" + encodeURIComponent(path) + "&line=" + row);
'''
p.write_text(s, encoding="utf-8", newline="\n")
print(s[-260:])
