import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/display/vnc.py"
s = p.read_text(encoding="utf-8")
old = """                            with open(config.RUN_DIR + "/ws.log", "a") as fh:
                                fh.write(msg.data.hex() + "\\n")"""
new = """                            with open(config.RUN_DIR + "/ws.log", "a") as fh:
                                fh.write("%d %s\\n" % (len(msg.data),
                                                      " ".join("%02x" % b for b in msg.data)))"""
assert old in s
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
