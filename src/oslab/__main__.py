"""Entry point: window, serve, or selftest."""
import argparse
import socket
import sys
import threading
import time

from . import config
from .backend.qemu.process import free_ports
from .core.errors import OsLabError
from .services import toolchain
from .services.session import Session
from .web import server, state


def instance_taken():
    probe = socket.socket()
    probe.settimeout(0.4)
    try:
        probe.connect((config.HOST, config.LOCK_PORT))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def prepare_tools(auto=True):
    """缺工具就装上；返回是否备齐。用户机器上可以什么都没有。"""
    todo = toolchain.missing_packages()
    if not todo:
        return True
    titles = "、".join(toolchain.WINDOWS[name]["title"] for name in todo)
    print("首次运行，缺 %s，开始下载到 .work/tools（只下一次）" % titles)
    if not auto:
        return False
    try:
        toolchain.ensure()
    except OsLabError as exc:
        print(exc)
        print("也可以自己装好，用 HATCH_NASM / HATCH_QEMU / HATCH_GCC 指过去")
        return False
    print("工具就绪")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hatch")
    parser.add_argument("action", nargs="?", choices=["setup", "run"], default="run")
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args(argv)

    if args.action == "setup":
        prepare_tools()
        for name, path, ready in toolchain.report():
            print("%-18s %s  %s" % (name, "就绪" if ready else "缺失", path))
        return 0 if not toolchain.missing() else 1

    if not prepare_tools():
        return 1

    if instance_taken():
        print("已有一个 hatch 在运行（端口 %d 被占用）" % config.LOCK_PORT)
        return 1

    lock = socket.socket()
    lock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lock.bind((config.HOST, config.LOCK_PORT))
    lock.listen(1)

    session = Session()
    state.install(session)
    free_ports()
    session.prepare()

    ready = threading.Event()
    server.start_thread(args.port, ready, lambda loop: session.source.start(loop))
    ready.wait(5)

    url = "http://%s:%d/" % (config.HOST, args.port)
    try:
        if args.serve:
            while True:
                time.sleep(1)
        elif args.browser:
            import webbrowser
            webbrowser.open(url)
            while True:
                time.sleep(1)
        else:
            import webview
            webview.create_window("hatch", url, width=1400, height=900,
                                  background_color="#0e1216")
            webview.start()
    finally:
        session.stop()
        lock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
