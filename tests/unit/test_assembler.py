"""Assembler: validation, 0xAA55 handling, floppy padding."""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab.core.errors import AssembleError  # noqa: E402
from oslab.services import assembler  # noqa: E402

GOOD = "BITS 16\nORG 0x7C00\nmov ax, 0x1234\njmp $\ntimes 510-($-$$) db 0\ndw 0xAA55\n"


def test_writes_bootable_image(workdir):
    out = workdir / "boot.img"
    assembler.assemble(GOOD, str(out))
    data = out.read_bytes()
    assert len(data) == 1474560
    assert data[510:512] == b"\x55\xaa"
    assert data[:2] == b"\xb8\x34"          # mov ax, 0x1234
    assert (workdir / "boot.img.dis.intel").exists()


def test_missing_signature_is_rejected(workdir):
    out = workdir / "boot.img"
    with pytest.raises(AssembleError, match="0xAA55"):
        assembler.assemble("BITS 16\nORG 0x7C00\njmp $\ntimes 512-($-$$) db 0\n", str(out))


def test_syntax_error_reports_line(workdir):
    out = workdir / "boot.img"
    with pytest.raises(AssembleError) as exc:
        assembler.assemble("BITS 16\nORG 0x7C00\nmov ax, \n", str(out))
    assert "boot.img.asm:3" in str(exc.value)


def test_too_large_source_is_rejected(workdir):
    out = workdir / "boot.img"
    body = "BITS 16\nORG 0x7C00\n" + "nop\n" * 2000000
    with pytest.raises(AssembleError, match="超过软盘容量"):
        assembler.assemble(body, str(out))
