"""Disassembly keeps both syntaxes, decodes as 16 bit, Intel by default."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from oslab.services import disasm  # noqa: E402

CODE = bytes.fromhex("fa31c08ed8ebfe") + b"\x90" * 8


def _image(tmp_path):
    image = tmp_path / "boot.img"
    payload = bytearray(512)
    payload[: len(CODE)] = CODE
    payload[510:512] = b"\x55\xaa"
    image.write_bytes(bytes(payload))
    disasm.build(str(image), 0x7C00)
    return str(image)


def test_both_syntaxes_are_written(tmp_path):
    image = _image(tmp_path)
    assert pathlib.Path(image + ".dis.intel").exists()
    assert pathlib.Path(image + ".dis.att").exists()


def test_default_is_intel(tmp_path):
    text = "\n".join(disasm.load(_image(tmp_path)))
    assert "xor    ax,ax" in text
    assert "%ax" not in text


def test_att_marks_registers(tmp_path):
    text = "\n".join(disasm.load(_image(tmp_path), "att"))
    assert "xor    %ax,%ax" in text


def test_unknown_syntax_falls_back_to_intel(tmp_path):
    text = "\n".join(disasm.load(_image(tmp_path), "wat"))
    assert "%ax" not in text


def test_missing_file_uses_the_other(tmp_path):
    image = _image(tmp_path)
    pathlib.Path(image + ".dis.intel").unlink()
    assert any("%ax" in line for line in disasm.load(image))
