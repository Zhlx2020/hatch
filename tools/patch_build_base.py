import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "services/build.py"
s = p.read_text(encoding="utf-8")
s = s.replace('''@register(".asm")
def _asm(text, path, image):
    include_dir = os.path.dirname(workspace.full(path)) or workspace.root()
    return assembler.assemble(text, image, includes=(include_dir,))''',
'''@register(".asm")
def _asm(text, path, image, base=None):
    include_dir = os.path.dirname(workspace.full(path, base)) or workspace.root(base)
    return assembler.assemble(text, image, includes=(include_dir,))''')
s = s.replace('''def build(text, path, image):
    handler = HANDLERS.get(workspace.ext(path))
    if handler is None:
        raise OsLabError("这个类型还不能运行：%s" % path)
    return handler(text, path, image)''',
'''def build(text, path, image, base=None):
    handler = HANDLERS.get(workspace.ext(path))
    if handler is None:
        raise OsLabError("这个类型还不能运行：%s" % path)
    return handler(text, path, image, base)''')
p.write_text(s, encoding="utf-8", newline="\n")

t = root.parent.parent / "tests/unit/test_build.py"
u = t.read_text(encoding="utf-8")
u = u.replace('build.build(MAIN, "boot/main.asm", image)', 'build.build(MAIN, "boot/main.asm", image, str(root))')
u = u.replace('build.build("int main(){}", "boot/main.c", str(pathlib.Path(workdir) / "x.img"))',
              'build.build("int main(){}", "boot/main.c",\n'
              '                str(pathlib.Path(workdir) / "x.img"), str(workdir))')
t.write_text(u, encoding="utf-8", newline="\n")
print("ok")
