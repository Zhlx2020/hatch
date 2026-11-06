import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/display/vnc.py"
s = p.read_text(encoding="utf-8")
old = """                    if self._writer:
                        try:
                            self._writer.write(msg.data)"""
new = """                    if self._writer:
                        try:
                            with open(config.RUN_DIR + "/ws.log", "a") as fh:
                                fh.write(msg.data.hex() + "\\n")
                            self._writer.write(msg.data)"""
assert old in s
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
