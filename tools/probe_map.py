import sys

sys.path.insert(0, "src")
from oslab.services import build, linemap, workspace  # noqa: E402

name = "t1-c/src/kmain.c"
text = workspace.read(name)
built, lm = build.build(text, name, ".run/probe/boot.img")
print("built", built, "map is None:", lm is None)
print("keys", list(lm or {})[:4])
print("lookup", linemap.lookup(lm, name, 9) if lm is not None else "no map")
