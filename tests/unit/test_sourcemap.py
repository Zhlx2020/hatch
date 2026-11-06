"""Source map: listing offsets become absolute lines, nearest wins."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab.services import sourcemap  # noqa: E402


def _listing(tmp_path, text):
    image = tmp_path / "boot.img"
    (tmp_path / "boot.img.lst").write_text(text, encoding="utf-8")
    return str(image)


def test_offsets_are_rebased(tmp_path):
    image = _listing(tmp_path, "     6 00000000 FA                          cli\n"
                               "     7 00000001 E460                        in al, 0x60\n")
    table = sourcemap.load(image)
    assert table[0x7C00] == 6
    assert table[0x7C01] == 7
    assert sourcemap.line_at(table, 0x7C01) == 7


def test_direct_addresses_are_kept(tmp_path):
    image = _listing(tmp_path, "     3 00007C10 90                          nop\n")
    table = sourcemap.load(image)
    assert table[0x7C10] == 3


def test_line_at_walks_back(tmp_path):
    image = _listing(tmp_path, "     9 00000000 E8 0000                     call 0\n")
    table = sourcemap.load(image)
    assert sourcemap.line_at(table, 0x7C03) == 9


def test_missing_listing_is_empty(tmp_path):
    assert sourcemap.load(str(tmp_path / "none.img")) == {}
    assert sourcemap.line_at({}, 0x7C00) == 0
