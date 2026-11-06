"""Aiohttp app assembly."""
import asyncio
import threading

from aiohttp import web

from .. import config
from . import routes


def build():
    app = web.Application()
    routes.install(app)
    app.router.add_static("/ui/", config.UI_DIR)
    return app


def run(port, ready=None, on_ready=None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    runner = web.AppRunner(build())
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, config.HOST, port)
    loop.run_until_complete(site.start())
    if on_ready:
        on_ready(loop)
    if ready:
        loop.call_soon(ready.set)
    loop.run_forever()


def start_thread(port, ready=None, on_ready=None):
    thread = threading.Thread(target=run, args=(port, ready, on_ready), daemon=True)
    thread.start()
    return thread
