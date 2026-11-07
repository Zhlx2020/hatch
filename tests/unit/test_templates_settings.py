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


def test_settings_round_trip(workdir):
    data = settings.save({"run": {"label": "跑", "hint": "说明", "action": "build",
                                  "pause_at_entry": False},
                          "qemu": {"profile": "cold", "extra": ["-fsdev", "local,path=x"]}},
                         str(workdir))
    assert data["qemu"]["profile"] == "cold"
    assert "-fsdev=local,path=x" in data["qemu"]["extra"]
    again = settings.load(str(workdir))
    assert again["run"]["action"] == "build"
    assert again["qemu"]["profile"] == "cold"


def test_settings_rejects_unknown_flag_and_profile(workdir):
    with pytest.raises(OsLabError, match="不认识"):
        settings.save({"qemu": {"extra": ["-nonsense"]}}, str(workdir))
    with pytest.raises(OsLabError, match="没有这个模板"):
        settings.save({"qemu": {"profile": "nope"}}, str(workdir))


def test_settings_rejects_managed_flags(workdir):
    with pytest.raises(OsLabError, match="模板管理"):
        settings.save({"qemu": {"extra": ["-m", "64"]}}, str(workdir))


def test_catalogue_has_tested_profiles():
    ids = {item["id"] for item in settings.catalogue()}
    assert {"floppy", "disk", "iso", "terminal", "q35"} <= ids
    for item in settings.catalogue():
        assert item["desc"] and item["screen"] in ("vnc", "serial")


def test_catalogue_spells_out_every_flag():
    """界面要能看见模板到底固定了什么，包括显卡和画面到底是哪种。"""
    for item in settings.catalogue():
        kinds = {row["k"] for row in item["rows"]}
        assert {"内存", "显卡", "画面", "串口"} <= kinds
        for row in item["rows"]:
            assert row["v"] and row["arg"].startswith("-")
    terminal = {row["k"]: row for row in
                next(i for i in settings.catalogue() if i["id"] == "terminal")["rows"]}
    assert "不装显卡" in terminal["显卡"]["v"]
    assert terminal["显卡"]["arg"] == "-vga none"
    assert "不开窗口" in terminal["画面"]["v"]
    floppy = {row["k"]: row for row in
              next(i for i in settings.catalogue() if i["id"] == "floppy")["rows"]}
    assert "能显示图形" in floppy["显卡"]["v"]


def test_profile_args_are_complete():
    """每个模板都得自己带启动设备与显示，托管项只留端口。"""
    for name in settings.PROFILES:
        args = settings.profile_args(name, "/tmp/x.img")
        assert "-boot" in args and "-m" in args and "-M" in args
        assert any(a.startswith("file=") or a == "/tmp/x.img" or
                   a.endswith("x.img") for a in args)
        assert "-display" in args
        assert "-gdb" not in args and "-serial" not in args


def test_qemu_command_uses_profile(workdir):
    from oslab.backend.qemu import process

    tune = {"run": {"pause_at_entry": False},
            "qemu": {"profile": "smp2", "extra": ["-no-reboot"]}}
    args = process.command("/tmp/x.img", tune)
    assert "-smp" in args and args[args.index("-smp") + 1] == "2"
    assert "-no-reboot" in args
    assert args[-1] == "-S"
    assert "-gdb" in args and "-serial" in args                

def test_runs_start_with_one_default(workdir):
    data = settings.load(str(workdir))
    assert data['active'] == settings.DEFAULT_NAME
    assert len(data['runs']) == 1
    assert data['runs'][0]['profile'] == settings.DEFAULT_PROFILE


def test_runs_can_hold_several_and_switch(workdir):
    data = settings.save({'runs': [
        {'name': '平时', 'label': '运行', 'profile': 'floppy'},
        {'name': '冷调试', 'label': '调试', 'profile': 'cold', 'pause_at_entry': False},
    ], 'active': '冷调试'}, str(workdir))
    assert data['active'] == '冷调试'
    assert data['qemu']['profile'] == 'cold'
    back = settings.load(str(workdir))
    assert [one['name'] for one in back['runs']] == ['平时', '冷调试']


def test_runs_reject_duplicate_and_empty(workdir):
    with pytest.raises(OsLabError, match='重复'):
        settings.save({'runs': [{'name': 'a'}, {'name': 'a'}]}, str(workdir))
    with pytest.raises(OsLabError, match='至少'):
        settings.save({'runs': []}, str(workdir))


def test_runs_switch_unknown_name_is_refused(workdir):
    with pytest.raises(OsLabError, match='没有这份配置'):
        settings.save({'active': '不在'}, str(workdir))


def test_old_single_run_file_migrates(workdir):
    (pathlib.Path(workdir) / settings.NAME).write_text(
        '[run]\nlabel = "老"\naction = "build"\n\n[qemu]\nprofile = "cold"\n',
        encoding='utf-8')
    data = settings.load(str(workdir))
    assert len(data['runs']) == 1 and data['runs'][0]['label'] == '老'
    assert data['qemu']['profile'] == 'cold'


def test_project_run_section_overrides_button(workdir):
    root = pathlib.Path(workdir)
    (root / 'p').mkdir()
    (root / 'p' / 'oslab.toml').write_text(
        'kind = "asm"\nentry = "a.asm"\n[run]\nlabel = "跑这个"\npause_at_entry = false\n',
        encoding='utf-8')
    (root / 'p' / 'a.asm').write_text('bits 16\n', encoding='utf-8')
    view = settings.with_project(settings.load(str(workdir)), 'p/a.asm', str(workdir))
    assert view['run']['label'] == '跑这个'
    assert view['run']['pause_at_entry'] is False
    assert view['from_project'] == 'p'
    assert view['qemu']['profile'] == settings.DEFAULT_PROFILE


def test_extra_survives_round_trip(workdir):
    settings.save({'qemu': {'extra': ['-fsdev', 'local,path=x']}}, str(workdir))
    assert settings.load(str(workdir))['qemu']['extra'] == ['-fsdev=local,path=x']
