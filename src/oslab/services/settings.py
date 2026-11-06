"""User-tunable start button and QEMU switches, validated before they are saved.

Everything lives in `workspace/settings.toml`. Extra QEMU arguments go through a
whitelist because the managed ones (ports, `-S`, `-drive`) would clash if the
user repeated them.
"""
import os

from ..core.errors import OsLabError
from . import workspace

NAME = "settings.toml"
RUN = {
    "label": "运行",
    "hint": "",
    "action": "run",          # run | build
    "pause_at_entry": True,
}
QEMU = {
    "memory": 32,
    "machine": "pc",
    "cpu": "",
    "extra": [],
}
# 允许放进 extra 的参数：都是独立开关，交给 QEMU 即可
ALLOWED = {
    "-no-reboot", "-no-shutdown", "-no-fd-bootchk", "-rtc", "-smp",
    "-accel", "-d", "-D", "-soundhw", "-machine", "-cpu", "-M",
    "-mem", "-m", "-vga", "-parallel", "-usb", "-usbdevice",
}
NEEDS_VALUE = {
    "-rtc", "-smp", "-accel", "-d", "-D", "-soundhw", "-machine", "-cpu",
    "-M", "-mem", "-m", "-vga", "-parallel", "-usbdevice",
}
MANAGED = {"-m": "内存", "-boot": "启动顺序", "-display": "显示",
           "-gdb": "调试端口", "-serial": "串口", "-monitor": "监视器",
           "-S": "入口暂停", "-drive": "镜像"}


def _path(base=None):
    return os.path.join(workspace.root(base), NAME)


def load(base=None):
    import tomllib

    data = {"run": dict(RUN), "qemu": dict(QEMU)}
    name = _path(base)
    if not os.path.exists(name):
        return data
    try:
        with open(name, "rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return data
    run = raw.get("run") or {}
    if isinstance(run.get("label"), str) and run["label"].strip():
        data["run"]["label"] = run["label"].strip()[:12]
    if isinstance(run.get("hint"), str):
        data["run"]["hint"] = run["hint"].strip()[:80]
    if run.get("action") in ("run", "build"):
        data["run"]["action"] = run["action"]
    if isinstance(run.get("pause_at_entry"), bool):
        data["run"]["pause_at_entry"] = run["pause_at_entry"]
    qemu = raw.get("qemu") or {}
    for key in ("memory", "machine", "cpu"):
        if key in qemu:
            try:
                data["qemu"][key] = _qemu_value(key, qemu[key])
            except OsLabError:
                continue
    if isinstance(qemu.get("extra"), list):
        try:
            data["qemu"]["extra"] = check_extra(qemu["extra"])
        except OsLabError:
            data["qemu"]["extra"] = []
    return data


def save(raw, base=None):
    """Validate then persist; raises with a readable reason when refused."""
    current = load(base)
    run = raw.get("run") or {}
    label = str(run.get("label", current["run"]["label"])).strip() or "运行"
    hint = str(run.get("hint", current["run"]["hint"])).strip()
    action = run.get("action", current["run"]["action"])
    if action not in ("run", "build"):
        raise OsLabError("按钮动作只能是 run 或 build")
    pause = run.get("pause_at_entry", current["run"]["pause_at_entry"])
    if not isinstance(pause, bool):
        raise OsLabError("入口暂停必须是真假值")

    qemu = raw.get("qemu") or {}
    values = dict(current["qemu"])
    for key in ("memory", "machine", "cpu"):
        if key in qemu:
            values[key] = _qemu_value(key, qemu[key])
    if "extra" in qemu:
        values["extra"] = check_extra(qemu["extra"])

    data = {
        "run": {"label": label[:12], "hint": hint[:80],
                "action": action, "pause_at_entry": pause},
        "qemu": values,
    }
    write(data, base)
    return data


def write(data, base=None):
    lines = ["# 由界面写入，可手工编辑", "", "[run]",
             'label = "%s"' % _esc(data["run"]["label"]),
             'hint = "%s"' % _esc(data["run"]["hint"]),
             'action = "%s"' % data["run"]["action"],
             "pause_at_entry = %s" % ("true" if data["run"]["pause_at_entry"] else "false"),
             "", "[qemu]",
             "memory = %d" % data["qemu"]["memory"],
             'machine = "%s"' % _esc(data["qemu"]["machine"]),
             'cpu = "%s"' % _esc(data["qemu"]["cpu"]),
             "extra = [%s]" % ", ".join('"%s"' % _esc(item)
                                       for item in data["qemu"]["extra"])]
    path = _path(base)
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _esc(text):
    return str(text).replace("\\", "\\\\").replace('"', '\\"')


def _qemu_value(key, value):
    if key == "memory":
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise OsLabError("内存要写数字（MB）")
        if not 4 <= number <= 512:
            raise OsLabError("内存要在 4 到 512 MB 之间")
        return number
    text = str(value or "").strip()
    if key == "machine" and not text:
        raise OsLabError("机器类型不能为空")
    if len(text) > 40:
        raise OsLabError("%s 太长" % key)
    return text


def check_extra(items):
    """One argument per entry; the flag must be whitelisted."""
    if not isinstance(items, list):
        raise OsLabError("附加参数要写成列表")
    out = []
    pending = None
    for raw in items:
        for part in str(raw).split():
            if part.startswith("-"):
                if part not in ALLOWED:
                    raise OsLabError("不认识的参数：%s" % part)
                if part in MANAGED:
                    raise OsLabError("%s 已经由界面管理" % part)
                if pending:
                    raise OsLabError("%s 缺少取值" % pending)
                if part in NEEDS_VALUE:
                    pending = part
                else:
                    out.append(part)
            else:
                if not pending:
                    raise OsLabError("多余的取值：%s" % part)
                out.append("%s=%s" % (pending, part) if pending in
                           ("-smp", "-rtc", "-vga", "-accel", "-machine",
                            "-cpu", "-M", "-mem", "-m", "-parallel", "-usbdevice")
                           else part)
                pending = None
    if pending:
        raise OsLabError("%s 缺少取值" % pending)
    if len(out) > 12:
        raise OsLabError("附加参数最多 12 项")
    return out
