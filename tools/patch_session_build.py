import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''            try:
                build.build(text, name, self.image)
                self.source_map = sourcemap.load(self.image)''',
'''            try:
                built, lines = build.build(text, name, self.image)
                self.source_map = sourcemap.load(self.image)
                self.line_map = lines or linemap.from_listing(self.image, name)''')

s = s.replace("from . import build, sourcemap", "from . import build, linemap, sourcemap")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
