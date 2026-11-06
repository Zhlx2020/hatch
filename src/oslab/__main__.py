"""Entry point: window, serve, or selftest."""
import argparse
import socket
import sys
import threading
import time

from . import config
from .backend.qemu.process import free_ports
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


def main(argv=None):
    parser = argparse.ArgumentParser(prog="oslab")
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args(argv)

    if instance_taken():
        print("已有一个 OS Lab 在运行（端口 %d 被占用）" % config.LOCK_PORT)
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
            webview.create_window("OS Lab", url, width=1400, height=900,
                                  background_color="#0e1216")
            webview.start()
    finally:
        session.stop()
        lock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
