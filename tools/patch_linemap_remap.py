import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services"

l = root / "linemap.py"
s = l.read_text(encoding="utf-8")
s = s.replace("def from_objects(objdump, image, plan, base=None):",
              "def from_objects(objdump, image, plan, base=None, remap=None):")
s = s.replace('''    root = workspace.root(base)''',
              '''    root = workspace.root(base)
    remap = {os.path.abspath(k).replace("\\\\", "/"): v for k, v in (remap or {}).items()}''')
s = s.replace('''        name, line = current
        rel = _rel(name, root)''',
              '''        name, line = current
        rel = remap.get(os.path.abspath(name).replace("\\\\", "/")) or _rel(name, root)''')
l.write_text(s, encoding="utf-8", newline="\n")

c = root / "cbuild.py"
t = c.read_text(encoding="utf-8")
t = t.replace("    objects = []\n", "    objects = []\n    remap = {}\n")
t = t.replace('''            src = staged''', '''            src = staged
            remap[staged] = source''')
t = t.replace("    return image, linemap.from_objects(config.OBJDUMP, kernel, plan)",
              "    return image, linemap.from_objects(config.OBJDUMP, kernel, plan,\n"
              "                                       base=base, remap=remap)")
c.write_text(t, encoding="utf-8", newline="\n")
print("ok")
