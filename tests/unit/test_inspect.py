"""磁盘布局与 ELF 两个可视化的解析层。"""
import pathlib
import struct
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab.core.errors import AssembleError  # noqa: E402
from oslab.services import diskmap, elfview  # noqa: E402

SECTOR = 512


def boot_sector(jump=b"\xeb\x3c\x90", tail=b"\x55\xaa", size=SECTOR):
    data = bytearray(b"\x00" * size)
    data[0:3] = jump
    data[3:11] = b"HATCH1.0"
    body = b"\xb4\x0e\xcd\x10" * 20
    data[62:62 + len(body)] = body
    data[510:512] = tail
    return bytes(data)


def write(workdir, data, parts):
    image = pathlib.Path(workdir) / "boot.img"
    image.write_bytes(data)
    diskmap.record(str(image), parts)
    return str(image)


def test_regions_come_from_the_build(workdir):
    image = write(workdir, boot_sector() + b"\x90" * SECTOR + b"\x00" * SECTOR,
                  [(0, SECTOR, "boot", "引导扇区", 0x7C00),
                   (SECTOR, SECTOR, "code", "负载", 0x7E00)])
    data = diskmap.describe(image)
    kinds = [row["kind"] for row in data["regions"]]
    assert kinds == ["boot", "code", "pad"]
    assert data["regions"][2]["size"] == SECTOR
    assert data["warnings"] == []


def test_signature_break_is_reported(workdir):
    image = write(workdir, boot_sector(tail=b"\x00\x00"), [])
    data = diskmap.describe(image)
    assert any("55 AA" in text for text in data["warnings"])


def test_mbr_is_decoded(workdir):
    data = bytearray(boot_sector())
    entry = bytearray(16)
    entry[0] = 0x80
    entry[4] = 0x0C
    entry[8:12] = (1).to_bytes(4, "little")
    entry[12:16] = (8).to_bytes(4, "little")
    data[0x1BE:0x1CE] = entry
    image = write(workdir, bytes(data), [])
    out = diskmap.describe(image)
    assert out["regions"][0]["kind"] == "mbr"
    fields = {row["k"]: row["v"] for row in out["regions"][0]["fields"]}
    assert "分区 1" in fields and "0x0C" in fields["分区 1"]


def test_line_marks_land_in_the_code_region(workdir):
    parts = [(0, SECTOR, "boot", "引导扇区", 0x7C00)]
    image = write(workdir, boot_sector() + b"\x90" * SECTOR, parts)
    out = diskmap.describe(image, [{"line": 4, "file": "a.asm", "addr": 0x7C04}])
    assert out["marks"][0]["offset"] == 4
    assert out["marks"][0]["line"] == 4


def test_gap_between_parts_is_flagged(workdir):
    image = write(workdir, b"\x00" * (SECTOR * 4),
                  [(0, SECTOR, "boot", "引导扇区", 0x7C00),
                   (SECTOR * 3, SECTOR, "code", "负载", 0x7E00)])
    kinds = [row["kind"] for row in diskmap.describe(image)["regions"]]
    assert "unknown" in kinds


def test_bare_image_still_gets_a_reading(workdir):
    image = pathlib.Path(workdir) / "raw.img"
    image.write_bytes(b"\x00" * SECTOR)
    data = diskmap.describe(str(image))
    assert data["size"] == SECTOR
    assert data["regions"][0]["kind"] == "boot"
    assert "没留记录" in data["regions"][0]["label"]


TABLE = 52
NAMES = TABLE + 80
TEXT = NAMES + 18


def _elf(entry=0x10000):
    """最小的 ELF32：头、两张节的表、字符串表，外加 8 字节代码。"""
    head = bytearray(52)
    head[0:4] = b"\x7fELF"
    head[4] = 1
    head[5] = 1
    struct.pack_into("<HHIIIIIHHHHHH", head, 16, 2, 3, 1, entry, 0, TABLE, 0, 52, 0, 0, 40, 2, 1)
    table = bytearray(80)
    struct.pack_into("<IIIIIIIIII", table, 0, 1, 1, 6, 0x10000, TEXT, 8, 0, 0, 4, 0)
    struct.pack_into("<IIIIIIIIII", table, 40, 7, 3, 0, 0, NAMES, 18, 0, 0, 1, 0)
    names = b"\x00.text\x00.data\x00.shstrtab\x00"
    return bytes(head) + bytes(table) + names + b"\x90" * 8


def test_elf_header_is_read(workdir):
    path = pathlib.Path(workdir) / "k.elf"
    path.write_bytes(_elf())
    data = elfview.describe(str(path))
    assert data["format"] == "elf" and data["machine"] == "i386"
    assert data["entry"] == 0x10000
    assert [one["name"] for one in data["sections"]] == [".text", ".data"]


def test_elf_entry_outside_code_is_flagged(workdir):
    path = pathlib.Path(workdir) / "k.elf"
    path.write_bytes(_elf())
    data = bytearray(_elf())
    struct.pack_into("<I", data, 24, 0x20000)   # entry 挪到 .text 之外
    path.write_bytes(bytes(data))
    out = elfview.describe(str(path))
    assert any("入口" in text for text in out["warnings"])
    assert out["sections"][0]["name"] == ".text"
    assert out["sections"][0]["flags"] == "AX"


def test_missing_elf_is_an_error(workdir):
    with pytest.raises(AssembleError, match="没有 ELF"):
        elfview.describe(str(pathlib.Path(workdir) / "none.elf"))
