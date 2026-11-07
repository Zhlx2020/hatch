"""User-tunable start button and QEMU switches, validated before they are saved.

QEMU 参数不再让用户拼：一组测过的模板（profile）固定下来，模板之外的再加附加参数。
模板只覆盖「把机器起对、起稳」这件事，附加参数负责个别实验。
"""
import os
import tomllib

from .. import config
from ..core.errors import OsLabError
from . import workspace

NAME = "settings.toml"
RUN = {
    "label": "运行",
    "hint": "",
    "action": "run",          # run | build
    "pause_at_entry": True,
}
# 模板：id -> 名字、说明、固定参数。参数里的 %s 是镜像路径。
PROFILES = {
    "floppy": {
        "name": "软盘 · VGA 画面",
        "desc": "默认档：512 字节引导扇区练习，软盘启动，串口留存做断言。",
        "args": ["-boot", "a", "-m", "32", "-M", "pc", "-vga", "std",
                 "-drive", "file=%s,if=floppy,format=raw"],
        "screen": "vnc",
    },
    "disk": {
        "name": "硬盘 · VGA 画面",
        "desc": "从 IDE 硬盘启动自己的系统：MBR、分区表、文件系统都在这条路上。",
        "args": ["-boot", "c", "-m", "64", "-M", "pc", "-vga", "std",
                 "-drive", "file=%s,if=ide,format=raw"],
        "screen": "vnc",
    },
    "iso": {
        "name": "光盘 · VGA 画面",
        "desc": "当成光盘启动，跑 El Torito 引导或整盘镜像。",
        "args": ["-boot", "d", "-m", "64", "-M", "pc", "-vga", "std", "-cdrom", "%s"],
        "screen": "vnc",
    },
    "terminal": {
        "name": "串口终端 · 无画面（纯文本）",
        "desc": "显卡整个关掉，只剩串口文本：Linux 内核、bootloader 这类只看文本的活用它。",
        "args": ["-boot", "c", "-m", "128", "-M", "pc", "-vga", "none",
                 "-drive", "file=%s,if=ide,format=raw"],
        "screen": "serial",
    },
    "smp2": {
        "name": "双核 · 128MB",
        "desc": "两核大内存：练 SMP 启动、AP 唤醒、锁和调度。",
        "args": ["-boot", "a", "-m", "128", "-M", "pc", "-vga", "std", "-smp", "2",
                 "-drive", "file=%s,if=floppy,format=raw"],
        "screen": "vnc",
    },
    "q35": {
        "name": "q35 · 64 位 CPU",
        "desc": "现代芯片组与长模式：PCIe、AHCI、x86_64 内核走这条。",
        "args": ["-boot", "c", "-m", "256", "-M", "q35", "-cpu", "qemu64", "-vga", "std",
                 "-drive", "file=%s,if=ide,format=raw"],
        "screen": "vnc",
    },
    "net": {
        "name": "带网卡 · 用户态网络",
        "desc": "e1000 + user 网络，DHCP 与 TCP 自带；练驱动和协议栈够用。",
        "args": ["-boot", "a", "-m", "64", "-M", "pc", "-vga", "std",
                 "-netdev", "user,id=n0", "-device", "e1000,netdev=n0",
                 "-drive", "file=%s,if=floppy,format=raw"],
        "screen": "vnc",
    },
    "cold": {
        "name": "冷调试档",
        "desc": "禁重启、禁关机：崩了就停在原地，好事后看现场。",
        "args": ["-boot", "a", "-m", "32", "-M", "pc", "-vga", "std", "-no-reboot", "-no-shutdown",
                 "-drive", "file=%s,if=floppy,format=raw"],
        "screen": "vnc",
    },
}
DEFAULT_PROFILE = "floppy"
QEMU = {
    "profile": DEFAULT_PROFILE,
    "extra": [],
}
# 允许放进 extra 的参数：都是独立开关，交给 QEMU 即可
ALLOWED = {
    "-no-reboot", "-no-shutdown", "-no-fd-bootchk", "-rtc", "-smp",
    "-accel", "-d", "-D", "-soundhw", "-usb", "-usbdevice",
    "-netdev", "-device", "-nic", "-chardev", "-fsdev", "-virtfs",
}
NEEDS_VALUE = {
    "-rtc", "-smp", "-accel", "-d", "-D", "-soundhw", "-usbdevice",
    "-netdev", "-device", "-nic", "-chardev", "-fsdev", "-virtfs",
}
JOIN = {"-smp", "-rtc", "-usbdevice", "-netdev", "-device", "-nic",
        "-chardev", "-fsdev", "-virtfs"}
# 模板已经给过的，用户再写就会撞
MANAGED = {"-m": "内存", "-boot": "启动顺序", "-display": "显示", "-vga": "显卡",
           "-M": "机器类型", "-machine": "机器类型", "-cpu": "CPU",
           "-gdb": "调试端口", "-serial": "串口", "-monitor": "监视器",
           "-S": "入口暂停", "-drive": "镜像", "-cdrom": "镜像"}


def _path(base=None):
    return os.path.join(workspace.root(base), NAME)


# 参数翻成人话：界面要把模板到底固定了什么摆出来，不能只给个名字
FLAGS = {
    "-m": ("内存", lambda v: v.replace(" ", "") + " MB"),
    "-M": ("机器类型", lambda v: {"pc": "老式 PC，i440FX 芯片组",
                                  "q35": "q35 芯片组，带 PCIe / AHCI"}.get(v, v)),
    "-machine": ("机器类型", lambda v: v),
    "-cpu": ("CPU", lambda v: "%s（QEMU 自带模型）" % v),
    "-boot": ("启动设备", lambda v: {"a": "软盘", "c": "硬盘", "d": "光盘"}.get(v, v)),
    "-vga": ("显卡", lambda v: "不装显卡，图形完全不可用" if v == "none"
             else "%s，能显示图形" % ("标准 VGA" if v == "std" else v)),
    "-smp": ("CPU 核数", lambda v: "%s 核" % v),
    "-netdev": ("网络", lambda v: "用户态网络，自带 DHCP 和 DNS"
                if v.split(",")[0] == "user" else v),
    "-device": ("外设", lambda v: "%s 网卡" % v.split(",")[0]),
    "-no-reboot": ("行为", lambda _v: "崩溃后不重启，停在现场"),
    "-no-shutdown": ("行为", lambda _v: "关机后 QEMU 不退出"),
}
IMAGE = {"if=floppy": "当成软盘挂上当前镜像", "if=ide": "当成 IDE 硬盘挂上当前镜像"}


def _drive_text(value):
    for key, text in IMAGE.items():
        if key in value:
            return text
    return "挂上当前镜像"


def describe(name):
    """把一个模板拆成「哪一项、设成什么、对应哪个参数」的行。"""
    item = PROFILES.get(name) or PROFILES[DEFAULT_PROFILE]
    rows = []
    args = list(item["args"])
    index = 0
    while index < len(args):
        flag = args[index]
        value = ""
        if index + 1 < len(args) and not args[index + 1].startswith("-"):
            value = args[index + 1]
            index += 1
        index += 1
        if flag == "-drive":
            rows.append({"k": "镜像", "v": _drive_text(value), "arg": ("-drive " + value).strip()})
            continue
        if flag == "-cdrom":
            rows.append({"k": "镜像", "v": "当成光盘挂上当前镜像",
                         "arg": ("-cdrom " + value).strip()})
            continue
        label, render = FLAGS.get(flag, (flag, lambda v: v))
        rows.append({"k": label, "v": render(value), "arg": (flag + " " + value).strip()})
    if item["screen"] == "vnc":
        rows.append({"k": "画面", "v": "开一个 VNC 窗口（127.0.0.1:%d），图形和文本都能看"
                     % config.RFB_PORT,
                     "arg": "-display vnc=127.0.0.1:%d" % config.VNC_HOST_PORT})
    else:
        rows.append({"k": "画面", "v": "不开窗口：屏幕那块直接显示串口文本",
                     "arg": "-display none"})
    rows.append({"k": "串口", "v": "独立收集，界面可以切过去看，不影响画面",
                 "arg": "-serial tcp:127.0.0.1:%d" % config.SERIAL_PORT})
    return rows


def catalogue():
    """界面用的模板清单。"""
    return [{"id": key, "name": item["name"], "desc": item["desc"],
             "screen": item["screen"], "rows": describe(key)}
            for key, item in PROFILES.items()]


def profile_args(name, image="%s"):
    """模板参数，带上显示方式：串口档关画面，其余走本地 VNC。"""
    item = PROFILES.get(name) or PROFILES[DEFAULT_PROFILE]
    args = [arg % image if "%s" in arg else arg for arg in item["args"]]
    if item["screen"] == "vnc":
        args += ["-display", "vnc=127.0.0.1:%d" % config.VNC_HOST_PORT]
    else:
        args += ["-display", "none"]
    return args


def screen_of(name):
    item = PROFILES.get(name) or PROFILES[DEFAULT_PROFILE]
    return item["screen"]


def _clean_run(raw):
    """按钮上的那几项，逐项校验。"""
    label = str(raw.get("label", RUN["label"])).strip() or RUN["label"]
    hint = str(raw.get("hint", "")).strip()
    action = raw.get("action", RUN["action"])
    if action not in ("run", "build"):
        raise OsLabError("按钮动作只能是 run 或 build")
    pause = raw.get("pause_at_entry", RUN["pause_at_entry"])
    if not isinstance(pause, bool):
        raise OsLabError("入口暂停必须是真假值")
    return {"label": label[:12], "hint": hint[:80], "action": action,
            "pause_at_entry": pause}


def _clean_qemu(raw):
    profile = raw.get("profile", QEMU["profile"])
    if profile not in PROFILES:
        raise OsLabError("没有这个模板：%s" % profile)
    extra = raw.get("extra", [])
    return {"profile": profile, "extra": check_extra(extra) if isinstance(extra, list) else []}


def load(base=None):
    data = {"run": dict(RUN), "qemu": dict(QEMU)}
    name = _path(base)
    if not os.path.exists(name):
        return data
    try:
        with open(name, "rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return data

    run, qemu = raw.get("run"), raw.get("qemu")
    legacy = next((item for item in raw.get("runs") or []
                   if isinstance(item, dict) and item.get("name") == raw.get("active")),
                  None)
    if legacy is None and isinstance(raw.get("runs"), list):
        legacy = next((item for item in raw["runs"]
                       if isinstance(item, dict) and "label" in item), None)
    if legacy is not None:          # 老文件是 [[runs]] + active：搬成一份
        run = {key: legacy[key] for key in RUN if key in legacy} if run is None else run
        qemu = legacy if qemu is None else qemu
    for value, target, clean in ((run, "run", _clean_run), (qemu, "qemu", _clean_qemu)):
        if not isinstance(value, dict):
            continue
        try:
            data[target] = clean(value)
        except OsLabError:
            pass
    return data


def save(raw, base=None):
    """Validate then persist; raises with a readable reason when refused."""
    data = load(base)
    run, qemu = raw.get("run"), raw.get("qemu")
    if isinstance(run, dict):
        data["run"] = _clean_run({**data["run"], **run})
    if isinstance(qemu, dict):
        data["qemu"] = _clean_qemu({**data["qemu"], **qemu})
    write(data, base)
    return data


def write(data, base=None):
    run, qemu = data["run"], data["qemu"]
    lines = ["# 由界面写入，可手工编辑",
             "[run]",
             'label = "%s"' % _esc(run["label"]),
             'hint = "%s"' % _esc(run["hint"]),
             'action = "%s"' % run["action"],
             "pause_at_entry = %s" % ("true" if run["pause_at_entry"] else "false"),
             "",
             "[qemu]",
             'profile = "%s"' % qemu["profile"],
             "extra = [%s]" % ", ".join('"%s"' % _esc(one) for one in qemu["extra"])]
    path = _path(base)
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _esc(text):
    return str(text).replace("\\", "\\\\").replace('"', '\\"')


def with_project(view, path, base=None):
    """按钮长相、入口暂停都只认运行配置；这里只记一下它在哪个工程里。"""
    from . import project

    try:
        directory = project.find(path, base)
    except OsLabError:
        directory = ""
    if directory:
        view["from_project"] = directory
    return view


def check_extra(items):
    """One argument per entry; the flag must be whitelisted."""
    if not isinstance(items, list):
        raise OsLabError("附加参数要写成列表")
    out = []
    pending = None
    for raw in items:
        for part in str(raw).split():
            if part.startswith("-"):
                # 存下来的形式是 -flag=value，读回来也要认
                head, _, tail = part.partition("=")
                if head in MANAGED:
                    raise OsLabError("%s 已经由模板管理" % head)
                if head not in ALLOWED:
                    raise OsLabError("不认识的参数：%s" % head)
                if pending:
                    raise OsLabError("%s 缺少取值" % pending)
                if tail:
                    out.append(part)
                elif head in NEEDS_VALUE:
                    pending = head
                else:
                    out.append(head)
            else:
                if not pending:
                    raise OsLabError("多余的取值：%s" % part)
                out.append("%s=%s" % (pending, part) if pending in JOIN
                           else "%s %s" % (pending, part))
                pending = None
    if pending:
        raise OsLabError("%s 缺少取值" % pending)
    if len(out) > 12:
        raise OsLabError("附加参数最多 12 项")
    return out
