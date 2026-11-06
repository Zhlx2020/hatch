"""C projects compile from the template into a bootable image."""
import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab.services import build  # noqa: E402

TEMPL = ROOT / "templ" / "c-hello"


def _project(workdir):
    target = pathlib.Path(workdir) / "proj"
    shutil.copytree(TEMPL, target)
    return target


def test_template_builds(workdir):
    project = _project(workdir)
    image = str(pathlib.Path(workdir) / "boot.img")
    out, lines = build.build(None, "proj/src/kmain.c", image, str(workdir))
    data = pathlib.Path(out).read_bytes()
    assert data[510:512] == b"\x55\xaa"
    assert len(data) == 1474560
    assert len(data) > 1024 and data[512:520] != b"\x00" * 8
    assert lines and any(lines.get("proj/src/kmain.c", {}).values())


def test_line_map_points_into_kernel(workdir):
    project = _project(workdir)
    image = str(pathlib.Path(workdir) / "boot.img")
    _, lines = build.build(None, "proj/src/kmain.c", image, str(workdir))
    lines_of_entry = lines["proj/src/kmain.c"]
    assert min(lines_of_entry.values()) >= 0x10000
    assert (project / "oslab.toml").exists()


def test_broken_c_reports_line(workdir):
    _project(workdir)
    image = str(pathlib.Path(workdir) / "boot.img")
    broken = "void _start(void)\n{\n    does_not_exist();\n}\n"
    with pytest.raises(Exception, match="kmain.c:3"):
        build.build(broken, "proj/src/kmain.c", image, str(workdir))
