import pathlib

import pytest

import oslab.services.bookmarks as bookmarks
import oslab.services.symbols as symbols
from oslab.core.errors import OsLabError
from oslab.services import workspace


@pytest.fixture()
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "root", lambda base=None: str(tmp_path))
    return tmp_path


def put(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return rel


def test_c_function_definition_ranks_first(root):
    put(root, "src/a.c", "void say(int x)\n{\n}\n")
    put(root, "src/a.h", "void say(int x);\n")
    put(root, "src/use.c", "void use(void)\n{\n    say(1);\n}\n")
    out = symbols.declarations("src/use.c", "say")
    assert out["kind"] == "c"
    assert out["hits"][0]["file"] == "src/a.c"
    assert out["hits"][0]["def"] is True
    assert out["hits"][0]["kind"] == "函数定义"
    rest = [row["kind"] for row in out["hits"][1:]]
    assert "函数声明" in rest


def test_macro_and_typedef_are_found(root):
    put(root, "src/a.h", "#define LIMIT 8\ntypedef unsigned int size_t2;\n")
    kinds = [row["kind"] for row in symbols.declarations("src/a.h", "LIMIT")["hits"]]
    assert kinds == ["宏"]
    kinds = [row["kind"] for row in symbols.declarations("src/a.h", "size_t2")["hits"]]
    assert kinds == ["类型"]


def test_asm_label_from_its_use(root):
    put(root, "src/boot.asm", "bits 16\n    jmp start\nstart:\n    hlt\n")
    out = symbols.declarations("src/boot.asm", "start")
    assert out["kind"] == "asm"
    assert out["hits"][0]["line"] == 3
    assert out["hits"][0]["kind"] == "标签"


def test_asm_needs_a_looking_like_word(root):
    put(root, "src/boot.asm", "mov ax, bx\n")
    with pytest.raises(OsLabError):
        symbols.declarations("src/boot.asm", "ax,bx")


def test_missing_word_is_rejected(root):
    put(root, "src/boot.asm", "hlt\n")
    with pytest.raises(OsLabError):
        symbols.declarations("src/boot.asm", "")


def test_unknown_name_gives_no_hits(root):
    put(root, "src/a.c", "int main(void) { return 0; }\n")
    assert symbols.declarations("src/a.c", "nope")["hits"] == []


def test_definition_in_another_file_still_wins(root):
    put(root, "src/a.c", "int thing(int v);\n")
    put(root, "z/deep/thing.c", "int thing(int v)\n{\n  return v;\n}\n")
    hits = symbols.declarations("src/a.c", "thing")["hits"]
    assert hits[0]["file"] == "z/deep/thing.c"  # 定义优先
    assert "src/a.c" in [row["file"] for row in hits]


def test_bookmark_round_trip(root):
    put(root, "src/a.c", "int main(void)\n{\n  return 0;\n}\n")
    out = bookmarks.toggle({"file": "src/a.c", "line": 2, "text": "{"})
    assert out["on"] is True
    assert out["marks"][0]["line"] == 2
    assert out["marks"][0]["missing"] is False
    again = bookmarks.toggle({"file": "src/a.c", "line": 2})
    assert again["on"] is False
    assert again["marks"] == []


def test_bookmark_survives_a_restart(root):
    put(root, "src/a.c", "x\n")
    bookmarks.toggle({"file": "src/a.c", "line": 1, "text": "x"})
    assert [row["file"] for row in bookmarks.load()] == ["src/a.c"]


def test_bookmark_of_a_vanished_file_is_kept_and_flagged(root):
    put(root, "src/a.c", "x\n")
    bookmarks.toggle({"file": "src/a.c", "line": 1})
    (root / "src/a.c").unlink()
    assert bookmarks.load()[0]["missing"] is True


def test_bookmark_needs_file_and_line(root):
    with pytest.raises(OsLabError):
        bookmarks.toggle({"line": 3})
    with pytest.raises(OsLabError):
        bookmarks.toggle({"file": "a.c", "line": 0})


def test_bookmark_remove_and_clear(root):
    put(root, "a.c", "1\n2\n")
    bookmarks.toggle({"file": "a.c", "line": 1})
    bookmarks.toggle({"file": "a.c", "line": 2})
    assert len(bookmarks.remove({"file": "a.c", "line": 1})["marks"]) == 1
    assert bookmarks.clear()["marks"] == []
    assert bookmarks.load() == []


def test_bookmark_text_is_truncated(root):
    put(root, "a.c", "x\n")
    out = bookmarks.toggle({"file": "a.c", "line": 1, "text": "y" * 500})
    assert len(out["marks"][0]["text"]) == 120


def test_bookmarks_file_lives_next_to_settings(root):
    put(root, "a.c", "x\n")
    bookmarks.toggle({"file": "a.c", "line": 1})
    assert pathlib.Path(bookmarks._path()).name == "bookmarks.json"
