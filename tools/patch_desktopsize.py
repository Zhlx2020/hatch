import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "display/vnc.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '        self._writer.write(struct.pack(">BxH", 2, 1) + struct.pack(">i", 0))',
    '        self._writer.write(struct.pack(">BxH", 2, 2) +\n'
    '                           struct.pack(">i", 0) + struct.pack(">i", -223))',
)
s = s.replace(
    '''                if enc == 0:
                    parts.append(await _readn(reader, w * h * 4))''',
    '''                if enc == -223:
                    self.width, self.height = w, h
                elif enc == 0:
                    parts.append(await _readn(reader, w * h * 4))''',
)
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "assets/ui/js/screen.js"
t = q.read_text(encoding="utf-8")
t = t.replace(
    '''        const px = new Uint8ClampedArray(take(w * h * 4));''',
    '''        if (enc === -223) {
          canvas.width = w;
          canvas.height = h;
        }
        if (enc !== 0) continue;
        const px = new Uint8ClampedArray(take(w * h * 4));''',
)
q.write_text(t, encoding="utf-8", newline="\n")

r = root / "assets/ui/styles/panels.css"
u = r.read_text(encoding="utf-8")
u = u.replace("  margin: auto;", "  margin: auto;\n  background: #000;")
r.write_text(u, encoding="utf-8", newline="\n")
print("ok")
