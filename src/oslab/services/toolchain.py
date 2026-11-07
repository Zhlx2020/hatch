"""外装工具：不需要用户先装好 qemu/nasm/gcc，缺了自己下到 .work/tools。

三件东西都有官方可直取的压缩包或静默安装器；装到项目目录里，不污染系统。
下载失败或系统不认识（非 Windows）时，退回环境变量与 PATH。
"""
import os
import re
import shutil
import time
import subprocess
import urllib.request
import zipfile

from .. import config
from ..core.errors import OsLabError

TOOLS_DIR = os.path.join(config.PROJECT, ".work", "tools")

# name -> 元信息；rel 是解包后二进制相对 TOOLS_DIR 的位置
WINDOWS = {
    "nasm": {
        "title": "NASM 汇编器",
        "url": "https://www.nasm.us/pub/nasm/releasebuilds/2.16.03/win64/nasm-2.16.03-win64.zip",
        "index": "https://www.nasm.us/pub/nasm/releasebuilds/2.16.03/win64/",
        "pattern": r"nasm-2\.16\.03-win64\.zip",
        "zip": True,
        "rel": ("nasm-2.16.03", "nasm.exe"),
    },
    "w64devkit": {
        "title": "w64devkit（gcc / ld / objcopy / objdump）",
        "url": "https://github.com/skeeto/w64devkit/releases/download/v1.23.0/w64devkit-1.23.0.zip",
        "zip": True,
        "rel": ("w64devkit", "bin", "gcc.exe"),
    },
    "qemu": {
        "title": "QEMU（i386 系统模拟）",
        "url": "https://qemu.weilnetz.de/w64/qemu-w64-setup-20260811.exe",
        "index": "https://qemu.weilnetz.de/w64/",
        "pattern": r"qemu-w64-setup-\d+\.exe",
        "zip": False,
        "rel": ("qemu", "qemu-system-i386.exe"),
    },
}

# 装好之后，这些路径就是 config 该用的
BINARIES = {
    "nasm": ("NASM", ("nasm-2.16.03", "nasm.exe")),
    "gcc": ("C_GCC", ("w64devkit", "bin", "gcc.exe")),
    "ld": ("C_LD", ("w64devkit", "bin", "ld.exe")),
    "objcopy": ("C_OBJCOPY", ("w64devkit", "bin", "objcopy.exe")),
    "objdump": ("OBJDUMP", ("w64devkit", "bin", "objdump.exe")),
    "qemu-system-i386": ("QEMU", ("qemu", "qemu-system-i386.exe")),
}


def path_of(rel):
    return os.path.join(TOOLS_DIR, *rel)


def _wanted():
    """当前机器该有哪些；非 Windows 交给系统包管理器。"""
    return WINDOWS if os.name == "nt" else {}


def _available(rel):
    target = path_of(rel)
    # 压缩包可能只解出目录却没解出可执行文件
    return os.path.isfile(target)


def _have(binary):
    """这个命令到底有没有：自带的、系统的、环境变量指的，都算。

    自己装过 qemu/gcc 的人不该被再下一遍。
    """
    attr = BINARIES[binary][0]
    return os.path.isfile(getattr(config, attr))


# 二进制 → 需要下的包（w64devkit 一次给四个）
PACKAGE_OF = {
    "nasm": "nasm",
    "gcc": "w64devkit",
    "ld": "w64devkit",
    "objcopy": "w64devkit",
    "objdump": "w64devkit",
    "qemu-system-i386": "qemu",
}


def missing():
    """返回还缺的命令名，界面和命令都用它说话。"""
    if os.name != "nt":
        return []
    return [binary for binary in BINARIES if not _have(binary)]


def missing_packages():
    """缺的命令折成要装的包，按 WINDOWS 里的顺序去重。"""
    need = {PACKAGE_OF[binary] for binary in missing()}
    return [name for name in WINDOWS if name in need]


def report():
    """给人看的现状：[(命令, 路径, 是否就绪)]。"""
    rows = []
    for binary, (attr, rel) in BINARIES.items():
        found = getattr(config, attr)
        rows.append((binary, found, _have(binary)))
    return rows


UA = {"User-Agent": "hatch-setup"}


def _fetch(url, timeout):
    """带浏览器 UA 和三次重试：释放站和 CDN 时不时会把连接掐掉。"""
    last = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(request, timeout=timeout)
        except OSError as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise last


def _download(url, target):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    resp = _fetch(url, 120)
    with resp, open(target, "wb") as out:
        shutil.copyfileobj(resp, out, 1 << 16)
    return target


def _unzip(archive, into):
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(into)


def _newest(url, index=None, pattern=None):
    """官方目录里取文件名最大的那个；取不到就用钉住的地址。"""
    if not index:
        return url
    try:
        with _fetch(index, 30) as resp:
            html = resp.read().decode("utf-8", "replace")
    except OSError:
        return url
    hits = sorted(set(re.findall(pattern, html)))
    return index + hits[-1] if hits else url


def _run_installer(installer, dest):
    """先直接跑；安装器清单要管理员时（WinError 740）再走 UAC 提权。"""
    try:
        done = subprocess.run([installer, "/S", "/D=" + dest], timeout=900)
        if done.returncode == 0:
            return
    except OSError as exc:
        if getattr(exc, "winerror", None) != 740:
            raise
    script = (
        "Start-Process -FilePath '%s' -ArgumentList '/S','/D=%s' -Verb RunAs -Wait"
        % (installer, dest))
    done = subprocess.run(["powershell", "-NoProfile", "-Command", script], timeout=900)
    if done.returncode != 0:
        raise OsLabError("QEMU 安装器需要管理员权限，提权也没成（返回 %d）" % done.returncode)


def install(name, log=print):
    """装一个工具到 TOOLS_DIR。失败抛 OsLabError，带人话原因。"""
    meta = _wanted().get(name)
    if not meta:
        raise OsLabError("这台机器不用装 %s，交给系统包管理器" % name)
    os.makedirs(TOOLS_DIR, exist_ok=True)
    url = _newest(meta["url"], meta.get("index"), meta.get("pattern"))
    target = os.path.join(TOOLS_DIR, os.path.basename(url))
    log("下载 %s：%s" % (meta["title"], url))
    try:
        _download(url, target)
    except OSError as exc:
        raise OsLabError("下载 %s 失败：%s（可手动装好后设 HATCH_%s 环境变量）"
                         % (meta["title"], exc, name.upper()))
    try:
        if meta["zip"]:
            _unzip(target, TOOLS_DIR)
        else:
            # QEMU 是 NSIS 安装器：静默装到项目目录，不写系统盘
            dest = os.path.join(TOOLS_DIR, "qemu")
            _run_installer(target, dest)
    except (OSError, zipfile.BadZipFile) as exc:
        raise OsLabError("展开 %s 失败：%s" % (meta["title"], exc))
    finally:
        if meta["zip"]:
            try:
                os.remove(target)
            except OSError:
                pass
    if not _available(meta["rel"]):
        raise OsLabError("%s 装完却没找到 %s" % (meta["title"], path_of(meta["rel"])))
    return path_of(meta["rel"])


def ensure(log=print):
    """缺什么装什么；返回装过的清单。"""
    todo = missing_packages()
    done, failed = [], []
    for name in todo:
        try:
            install(name, log)
            done.append(name)
        except OsLabError as exc:
            failed.append((name, str(exc)))
            log("跳过 %s：%s" % (name, exc))
    if failed and len(failed) == len(todo):
        raise OsLabError("; ".join(msg for _, msg in failed))
    return done
