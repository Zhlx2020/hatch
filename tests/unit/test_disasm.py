"""Static disassembly map: builds, loads and answers by address."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from oslab.services import disasm  # noqa: E402

CODE = bytes.fromhex("fa31c08ed8ebfe") + b"\x90" * 8


def test_build_and_lookup(tmp_path):
    image = tmp_path / "boot.img"
    payload = bytearray(512)
    payload[: len(CODE)] = CODE
    payload[510:512] = b"\x55\xaa"
    image.write_bytes(bytes(payload))

    disasm.build(str(image), 0x7C00)
    lines = disasm.load(str(image))
    assert lines

    text = disasm.around(lines, 0x7C00, 3)
    assert "cli" in text
    assert text.splitlines()[0].startswith("00007c00")


def test_around_past_end_returns_tail(tmp_path):
    image = tmp_path / "boot.img"
    payload = bytearray(512)
    payload[:2] = b"\xeb\xfe"
    image.write_bytes(bytes(payload))
    disasm.build(str(image), 0x7C00)

    lines = disasm.load(str(image))
    text = disasm.around(lines, 0xFFFF, 4)
    assert "jmp" in text
