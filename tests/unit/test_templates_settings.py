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


def _manifest(root, text):
    (root / "p").mkdir(exist_ok=True)
    (root / "p" / "oslab.toml").write_text(text, encoding="utf-8")


def test_manifest_refuses_typo_and_misplaced_keys(workdir):
    root = pathlib.Path(workdir)
    _manifest(root, 'kind = "asm"\nentry = "a.asm"\nsouces = ["b.asm"]\n')
    with pytest.raises(OsLabError, match="不认识的键 souces"):
        project.load("p", str(root))
    _manifest(root, 'kind = "asm"\nentry = "a.asm"\nboot = "boot.asm"\n')
    with pytest.raises(OsLabError, match="只有 C 工程"):
        project.load("p", str(root))


def test_manifest_entry_must_be_in_sources(workdir):
    root = pathlib.Path(workdir)
    (root / "p").mkdir()
    for name in ("a.c", "b.c", "boot.asm", "kernel.ld"):
        (root / "p" / name).write_text("", encoding="utf-8")
    _manifest(root, 'kind = "c"\nentry = "a.c"\nsources = ["b.c"]\n'
                     'boot = "boot.asm"\nlink = "kernel.ld"\n')
    with pytest.raises(OsLabError, match="entry 得在 sources 里"):
        project.load("p", str(root))
    _manifest(root, 'kind = "c"\nentry = "a.c"\nboot = "boot.asm"\nlink = "kernel.ld"\n')
    assert project.load("p", str(root))["sources"] == ["p/a.c"]


def test_manifest_base_takes_hex_text_and_checks_range(workdir):
    root = pathlib.Path(workdir)
    (root / "p").mkdir()
    (root / "p" / "a.asm").write_text("bits 16\n", encoding="utf-8")
    _manifest(root, 'kind = "asm"\nentry = "a.asm"\nbase = "0x600"\n')
    assert project.load("p", str(root))["base"] == 0x600
    _manifest(root, 'kind = "asm"\nentry = "a.asm"\nbase = 0x9000\n')
    with pytest.raises(OsLabError, match="0x500 到 0x7C00"):
        project.load("p", str(root))
    _manifest(root, 'kind = "asm"\nentry = "a.asm"\nbase = 0x100\n')
    with pytest.raises(OsLabError, match="0x500 到 0x7C00"):
        project.load("p", str(root))
    _manifest(root, 'kind = "asm"\nentry = "a.asm"\nbase = 0x605\n')
    with pytest.raises(OsLabError, match="16 字节对齐"):
        project.load("p", str(root))
    _manifest(root, 'kind = "asm"\nentry = "a.asm"\nbase = "seven"\n')
    with pytest.raises(OsLabError, match="地址"):
        project.load("p", str(root))


def test_shipped_manifests_still_load(workdir):
    for name in ("asm-hello", "c-hello"):
        templates.apply(name, name, str(workdir))
        plan = project.load(name, str(workdir))
        assert plan["kind"] in ("asm", "c") and plan["base"] == 0x7C00


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

def test_settings_start_at_defaults(workdir):
    data = settings.load(str(workdir))
    assert data["run"]["label"] == "运行"
    assert data["run"]["action"] == "run"
    assert data["qemu"]["profile"] == settings.DEFAULT_PROFILE


def test_button_fields_are_saved_one_by_one(workdir):
    settings.save({"run": {"label": "构建"}}, str(workdir))
    data = settings.save({"run": {"action": "build", "pause_at_entry": False}}, str(workdir))
    assert data["run"]["label"] == "构建"       # 上一次改的没被冲掉
    assert data["run"]["action"] == "build"
    assert settings.load(str(workdir))["run"]["pause_at_entry"] is False


def test_bad_values_are_refused(workdir):
    with pytest.raises(OsLabError, match="run 或 build"):
        settings.save({"run": {"action": "delete"}}, str(workdir))
    with pytest.raises(OsLabError, match="真假值"):
        settings.save({"run": {"pause_at_entry": "yes"}}, str(workdir))
    with pytest.raises(OsLabError, match="没有这个模板"):
        settings.save({"qemu": {"profile": "nope"}}, str(workdir))


def test_multi_run_file_migrates(workdir):
    (pathlib.Path(workdir) / settings.NAME).write_text(
        'active = "冷档"\n\n[[runs]]\nname = "平时"\nlabel = "运行"\n\n'
        '[[runs]]\nname = "冷档"\nlabel = "调试"\naction = "build"\nprofile = "cold"\n',
        encoding="utf-8")
    data = settings.load(str(workdir))
    assert data["run"]["label"] == "调试"
    assert data["run"]["action"] == "build"
    assert data["qemu"]["profile"] == "cold"


def test_project_no_longer_changes_the_button(workdir):
    root = pathlib.Path(workdir)
    (root / 'p').mkdir()
    (root / 'p' / 'oslab.toml').write_text(
        'kind = "asm"\nentry = "a.asm"\n', encoding='utf-8')
    (root / 'p' / 'a.asm').write_text('bits 16\n', encoding='utf-8')
    saved = settings.load(str(workdir))
    view = settings.with_project(saved, 'p/a.asm', str(workdir))
    assert view['run'] == saved['run']
    assert view['from_project'] == 'p'
    assert view['qemu']['profile'] == settings.DEFAULT_PROFILE


def test_leftover_run_block_is_rejected(workdir):
    root = pathlib.Path(workdir)
    (root / 'p').mkdir()
    (root / 'p' / 'a.asm').write_text('bits 16\n', encoding='utf-8')
    (root / 'p' / 'oslab.toml').write_text(
        'kind = "asm"\nentry = "a.asm"\n[run]\nlabel = "跑这个"\npause_at_entry = false\n',
        encoding='utf-8')
    with pytest.raises(OsLabError) as caught:
        project.load('p', str(workdir))
    assert '[run]' in str(caught.value)
    assert 'label' in str(caught.value)


def test_extra_survives_round_trip(workdir):
    settings.save({'qemu': {'extra': ['-fsdev', 'local,path=x']}}, str(workdir))
    assert settings.load(str(workdir))['qemu']['extra'] == ['-fsdev=local,path=x']
