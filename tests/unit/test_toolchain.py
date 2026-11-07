"""工具自带：缺什么装什么，路径能落到 config 上。"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab import config  # noqa: E402
from oslab.core.errors import OsLabError  # noqa: E402
from oslab.services import toolchain  # noqa: E402


def test_tools_dir_lives_under_work():
    assert toolchain.TOOLS_DIR == str(ROOT / ".work" / "tools")


def test_managed_copy_wins_over_hints():
    """解析顺序里项目自带的工具要压过备用目录，用户机器上才不用先装。"""
    probe = pathlib.Path(toolchain.TOOLS_DIR) / "_probe" / "tool.exe"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_bytes(b"MZ")
    fallback = str(ROOT / "nowhere" / "tool.exe")
    try:
        assert config._tool("hatch-probe-none", "HATCH_PROBE", str(probe), fallback) \
            == str(probe)
    finally:
        if probe.exists():
            probe.unlink()


def test_missing_reports_absent_binaries():
    absent = toolchain.missing()
    for name in absent:
        assert name in toolchain.WINDOWS
        assert not toolchain._available(toolchain.WINDOWS[name]["rel"])


def test_install_rejects_unknown_tool():
    try:
        toolchain.install("nope")
    except OsLabError as exc:
        assert "不用装" in str(exc)
    else:
        raise AssertionError("该报错")


def test_newest_falls_back_without_index():
    assert toolchain._newest("http://x/y.zip") == "http://x/y.zip"


def test_report_covers_every_binary():
    rows = toolchain.report()
    assert {row[0] for row in rows} == set(toolchain.BINARIES)
    for _, path, ready in rows:
        assert path
        assert isinstance(ready, bool)


def test_missing_packages_are_deduped():
    """缺四个 gcc 家族命令时只该下一个 w64devkit。"""
    packages = toolchain.missing_packages()
    assert len(packages) == len(set(packages))
    for name in packages:
        assert name in toolchain.WINDOWS


def test_installed_tools_count_as_present():
    """自己装过 qemu/gcc 的机器不该被再下一遍。"""
    for binary in toolchain.BINARIES:
        attr = toolchain.BINARIES[binary][0]
        assert toolchain._have(binary) == os.path.isfile(getattr(config, attr))
