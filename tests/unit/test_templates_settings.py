"""Templates: list and apply, and the manifest-driven build path."""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab.core.errors import OsLabError  # noqa: E402
from oslab.services import project, settings, templates  # noqa: E402


def test_templates_are_listed():
    names = [item["name"] for item in templates.entries()]
    assert "asm-hello" in names and "c-hello" in names


def test_apply_copies_and_reports_entry(workdir):
    out = templates.apply("asm-hello", "demo", str(workdir))
    assert out["entry"] == "demo/boot.asm"
    assert (pathlib.Path(workdir) / "demo" / "oslab.toml").exists()


def test_apply_refuses_non_empty_target(workdir):
    templates.apply("asm-hello", "demo", str(workdir))
    with pytest.raises(OsLabError, match="不是空的"):
        templates.apply("c-hello", "demo", str(workdir))


def test_unknown_template(workdir):
    with pytest.raises(OsLabError, match="没有这个模板"):
        templates.apply("nope", "x", str(workdir))


def test_manifest_validation(workdir):
    root = pathlib.Path(workdir)
    (root / "p").mkdir()
    (root / "p" / "oslab.toml").write_text('kind = "c"\nentry = "a.c"\n', encoding="utf-8")
    with pytest.raises(OsLabError, match="boot"):
        project.load("p", str(root))
    (root / "p" / "oslab.toml").write_text('kind = "nope"\nentry = "a.c"\n', encoding="utf-8")
    with pytest.raises(OsLabError, match="kind"):
        project.load("p", str(root))


def test_settings_round_trip_and_whitelist(workdir):
    data = settings.save({"run": {"label": "跑", "hint": "说明", "action": "build",
                                  "pause_at_entry": False},
                          "qemu": {"memory": 48, "machine": "isapc",
                                   "extra": ["-no-reboot", "-smp", "2"]}},
                         str(workdir))
    assert data["qemu"]["memory"] == 48
    assert "-smp=2" in data["qemu"]["extra"]
    again = settings.load(str(workdir))
    assert again["run"]["action"] == "build"
    assert again["qemu"]["machine"] == "isapc"


def test_settings_rejects_unknown_and_managed(workdir):
    with pytest.raises(OsLabError, match="不认识"):
        settings.save({"qemu": {"extra": ["-nonsense"]}}, str(workdir))
    with pytest.raises(OsLabError, match="界面管理"):
        settings.save({"qemu": {"extra": ["-m", "64"]}}, str(workdir))


def test_settings_memory_bounds(workdir):
    with pytest.raises(OsLabError, match="4 到 512"):
        settings.save({"qemu": {"memory": 2}}, str(workdir))


def test_qemu_command_uses_settings(workdir):
    from oslab.backend.qemu import process

    tune = {"run": {"pause_at_entry": False},
            "qemu": {"memory": 64, "machine": "isapc", "cpu": "486",
                     "extra": ["-no-reboot"]}}
    args = process.command("/tmp/x.img", tune)
    assert "-m" in args and args[args.index("-m") + 1] == "64"
    assert "isapc" in args and "486" in args and "-no-reboot" in args
    assert "-S" in args
