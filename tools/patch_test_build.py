import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tests/unit/test_build.py"
s = p.read_text(encoding="utf-8")
s = s.replace('''def test_unsupported_extension_is_rejected(workdir):
    with pytest.raises(OsLabError, match="不能运行"):
        build.build("int main(){}", "boot/main.c",
                str(pathlib.Path(workdir) / "x.img"), str(workdir))


def test_c_is_reserved_but_not_runnable():
    assert not build.supported("a.c")
    assert build.supported("a.asm")''',
'''def test_unsupported_extension_is_rejected(workdir):
    with pytest.raises(OsLabError, match="不能运行"):
        build.build("print 1", "boot/notes.txt",
                    str(pathlib.Path(workdir) / "x.img"), str(workdir))


def test_c_without_manifest_says_so(workdir):
    with pytest.raises(OsLabError, match="oslab.toml"):
        build.build("int main(){}", "main.c",
                    str(pathlib.Path(workdir) / "x.img"), str(workdir))


def test_c_is_runnable_by_suffix():
    assert build.supported("a.c")
    assert build.supported("a.asm")''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
