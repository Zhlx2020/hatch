"""Workspace tree: path safety and node operations."""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab.core.errors import OsLabError  # noqa: E402
from oslab.services import workspace  # noqa: E402


@pytest.mark.parametrize("bad", ["../x", "a/../../b", "a b.asm"])
def test_safe_rejects_traversal(bad):
    with pytest.raises(OsLabError):
        workspace.safe(bad)


def test_safe_normalises_edges():
    assert workspace.safe("/abs.asm") == "abs.asm"
    assert workspace.safe("a\\b.asm") == "a/b.asm"
    assert workspace.safe("./a.asm") == "a.asm"
    assert workspace.safe("a//x.asm") == "a/x.asm"


def test_tree_is_nested_and_ordered(workdir):
    workspace.mkdir("zdir", str(workdir))
    workspace.touch("zdir/inner.asm", str(workdir))
    workspace.touch("b.asm", str(workdir))
    nodes = workspace.tree(str(workdir))
    assert nodes[0]["kind"] == "dir"
    assert nodes[0]["children"][0]["path"] == "zdir/inner.asm"
    assert nodes[1]["path"] == "b.asm"


def test_unknown_extension_is_hidden(workdir):
    (pathlib.Path(workdir) / "note.log").write_text("x")
    assert workspace.tree(str(workdir)) == []


def test_touch_writes_template(workdir):
    workspace.touch("boot/kernel.asm", str(workdir))
    text = workspace.read("boot/kernel.asm", str(workdir))
    assert "0xaa55" in text


def test_touch_refuses_existing(workdir):
    workspace.touch("a.asm", str(workdir))
    with pytest.raises(OsLabError):
        workspace.touch("a.asm", str(workdir))


def test_rename_and_collision(workdir):
    workspace.touch("a.asm", str(workdir))
    workspace.touch("b.asm", str(workdir))
    assert workspace.rename("a.asm", "c.asm", str(workdir)) == "c.asm"
    with pytest.raises(OsLabError):
        workspace.rename("c.asm", "b.asm", str(workdir))


def test_move_into_directory(workdir):
    workspace.mkdir("boot", str(workdir))
    workspace.touch("a.asm", str(workdir))
    assert workspace.move("a.asm", "boot", str(workdir)) == "boot/a.asm"


def test_remove_directory_is_recursive(workdir):
    workspace.mkdir("boot", str(workdir))
    workspace.touch("boot/a.asm", str(workdir))
    workspace.remove("boot", str(workdir))
    assert workspace.tree(str(workdir)) == []


def test_entry_file_prefers_first_runnable(workdir):
    workspace.touch("readme.md", str(workdir))
    workspace.touch("boot/start.asm", str(workdir))
    assert workspace.entry_file(str(workdir)) == "boot/start.asm"


def test_write_creates_missing_parents(workdir):
    workspace.write("deep/a/b.asm", "x", str(workdir))
    assert (pathlib.Path(workdir) / "deep/a/b.asm").read_text() == "x"
