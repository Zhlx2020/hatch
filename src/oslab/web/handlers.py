"""Request handlers: thin, no business logic."""
import asyncio
import os

from aiohttp import web

from .. import config
from ..core.errors import OsLabError
from ..services import checker, settings, templates, workspace
from . import state as shared


def session():
    found = shared.session()
    if not found:
        raise web.HTTPServiceUnavailable(text="no session")
    return found


async def index(_request):
    return web.FileResponse(os.path.join(config.UI_DIR, "index.html"))


async def state(_request):
    return web.json_response(await asyncio.to_thread(session().snapshot))


# workspace -----------------------------------------------------------
async def tree(_request):
    return web.json_response(await asyncio.to_thread(workspace.tree))


async def node_create(request):
    body = await request.json()
    path = body.get("path", "")
    try:
        if body.get("kind") == "dir":
            await asyncio.to_thread(workspace.mkdir, path)
        else:
            await asyncio.to_thread(workspace.touch, path)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"path": path})


async def node_rename(request):
    body = await request.json()
    try:
        moved = await asyncio.to_thread(workspace.rename, body.get("path", ""),
                                        body.get("name", ""))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"path": moved})


async def node_move(request):
    body = await request.json()
    try:
        moved = await asyncio.to_thread(workspace.move, body.get("path", ""),
                                        body.get("dir", ""))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"path": moved})


async def node_delete(request):
    path = request.query.get("path", "")
    try:
        await asyncio.to_thread(workspace.remove, path)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"path": path})


async def file_read(request):
    path = request.match_info["path"]
    try:
        text = await asyncio.to_thread(workspace.read, path)
    except OsLabError as exc:
        raise web.HTTPNotFound(text=str(exc)) from exc
    return web.json_response({"path": path, "text": text})


async def file_write(request):
    path = request.match_info["path"]
    body = await request.json()
    try:
        await asyncio.to_thread(workspace.write, path, body.get("text", ""))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"path": path})


# observation ----------------------------------------------------------
async def regs(_request):
    try:
        return web.json_response(await asyncio.to_thread(session().reg_detail))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)


async def reg_set(request):
    body = await request.json()
    value = int(str(body.get("value", "0")), 0) & 0xFFFFFFFF
    try:
        out = await asyncio.to_thread(session().set_reg, body.get("name", ""), value)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"value": out})


async def mem(request):
    body = await request.json()
    addr = int(str(body.get("addr", "0")), 16)
    count = int(body.get("count", 256))
    try:
        out = await asyncio.to_thread(session().mem_rows, addr, count)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(out)


async def line(request):
    """Address of a source line in the last build; 0 when unmapped."""
    path = request.query.get("path", "")
    line = int(request.query.get("line", "0") or 0)
    current = session()
    addr = current.line_addr(path, line)
    reason = "" if addr else "还没构建过这个文件，或者这行没有代码"
    return web.json_response({"addr": "%08x" % addr if addr else "", "reason": reason})


async def disasm(request):
    body = await request.json()
    addr = int(str(body.get("addr", "0")), 16)
    count = int(body.get("count", 32))
    syntax = (body.get("syntax") or "intel").lower()
    if syntax not in ("intel", "att"):
        syntax = "intel"
    try:
        out = await asyncio.to_thread(session().disasm_rows, addr, count, syntax)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(out)


async def check(request):
    body = await request.json()
    path = body.get("path", "")
    try:
        result = await asyncio.to_thread(checker.check, path, body.get("text", ""))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(result)


# control -------------------------------------------------------------
async def templates_list(request):
    return web.json_response(templates.entries())


async def templates_apply(request):
    body = await request.json()
    try:
        out = await asyncio.to_thread(templates.apply, body.get("name", ""),
                                      body.get("dir", ""))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(out)


async def settings_get(request):
    return web.json_response(settings.load())


async def settings_put(request):
    body = await request.json()
    try:
        data = settings.save(body)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(data)


async def run(request):
    body = await request.json()
    name = body.get("name", "")
    lines = [int(item) for item in (body.get("lines") or []) if str(item).isdigit()]
    try:
        if body.get("build") and not lines:
            result = await asyncio.to_thread(session().build_only, workspace.read(name), name)
        else:
            result = await asyncio.to_thread(session().run_file, name, lines)
        return web.json_response(result)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except (OSError, TimeoutError) as exc:
        return web.json_response({"error": "启动失败：%s" % exc}, status=500)


async def step(_request):
    return await _action(lambda s: s.step())


async def step_over(_request):
    return await _action(lambda s: s.step_over())


async def cont(_request):
    return await _action(lambda s: s.cont())


async def serial(_request):
    return web.json_response({"text": await asyncio.to_thread(session().serial_tail)})


async def pause(_request):
    return await _action(lambda s: s.pause())


async def reset(_request):
    return await _action(lambda s: s.reset())


async def _action(fn):
    try:
        out = await asyncio.to_thread(fn, session())
        return web.json_response({"output": out})
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)


# observation ---------------------------------------------------------
async def bp_add(request):
    body = await request.json()
    return await _action(lambda s: s.add_breakpoint(int(body["addr"], 16)))


async def bp_del(request):
    addr = request.match_info["addr"]
    return await _action(lambda s: s.remove_breakpoint(int(addr, 16)))


async def bp_list(_request):
    return web.json_response({"list": await asyncio.to_thread(session().breakpoints)})


async def tables(_request):
    return web.json_response(await asyncio.to_thread(session().tables))


async def screen(request):
    ws = web.WebSocketResponse(max_msg_size=0)
    await ws.prepare(request)
    await session().source.attach(ws)
    return ws
