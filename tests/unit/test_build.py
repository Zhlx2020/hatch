"""Build dispatch: extension routing and include resolution."""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab.core.errors import OsLabError  # noqa: E402
from oslab.services import build, workspace  # noqa: E402

MAIN = """bits 16
org 0x7c00
    jmp start
%include "banner.inc"
start:
    cli
    say hi
    hlt
hi: db "HI", 13, 10, 0
times 510-($-$$) db 0
dw 0xaa55
"""

BANNER = """%macro say 1
    mov si, %1
    call puts
%endmacro
puts:
    lodsb
    test al, al
    jz .end
    mov ah, 0x0e
    int 0x10
    jmp puts
.end:
    ret
"""


def test_asm_build_uses_include_dir(workdir):
    root = pathlib.Path(workdir)
    workspace.mkdir("boot", str(root))
    workspace.write("boot/banner.inc", BANNER, str(root))
    image = str(root / "boot.img")
    build.build(MAIN, "boot/main.asm", image)
    assert pathlib.Path(image).read_bytes()[510:512] == b"\x55\xaa"


def test_unsupported_extension_is_rejected(workdir):
    with pytest.raises(OsLabError, match="不能运行"):
        build.build("int main(){}", "boot/main.c", str(pathlib.Path(workdir) / "x.img"))


def test_c_is_reserved_but_not_runnable():
    assert not build.supported("a.c")
    assert build.supported("a.asm")
