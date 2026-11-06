"""Checker: reports lines for assemble errors, skips unrunnable types."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab.services import checker  # noqa: E402

BAD = "bits 16\norg 0x7c00\nmov ax,\nhlt\n"
GOOD = "bits 16\norg 0x7c00\nhlt\ntimes 510-($-$$) db 0\ndw 0xaa55\n"


def test_reports_error_line():
    out = checker.check("boot/a.asm", BAD)
    assert out["ok"] is False
    assert out["errors"][0]["line"] == 3
    assert "operands" in out["errors"][0]["message"]


def test_accepts_valid_source():
    out = checker.check("boot/a.asm", GOOD)
    assert out["ok"] is True
    assert out["errors"] == []


def test_include_file_is_skipped():
    out = checker.check("boot/a.inc", "%macro x 1\n%endmacro\n")
    assert out["ok"] is True and out.get("skipped") is True
