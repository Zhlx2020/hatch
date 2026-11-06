import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "web/handlers.py"
s = p.read_text(encoding="utf-8")

old = s[s.index("# files ---------------------------------------------------------------"):s.index("# control -------------------------------------------------------------")]
new = '''# workspace -----------------------------------------------------------
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


'''
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")

r = root / "web/routes.py"
t = r.read_text(encoding="utf-8")
t = t.replace('    ("GET", "/api/files", handlers.files),\n'
              '    ("POST", "/api/files", handlers.file_create),\n'
              '    ("GET", "/api/files/{name}", handlers.file_read),\n'
              '    ("PUT", "/api/files/{name}", handlers.file_write),\n'
              '    ("DELETE", "/api/files/{name}", handlers.file_delete),',
              '    ("GET", "/api/tree", handlers.tree),\n'
              '    ("POST", "/api/node", handlers.node_create),\n'
              '    ("POST", "/api/node/rename", handlers.node_rename),\n'
              '    ("POST", "/api/node/move", handlers.node_move),\n'
              '    ("DELETE", "/api/node", handlers.node_delete),\n'
              '    ("GET", "/api/file/{path:.+}", handlers.file_read),\n'
              '    ("PUT", "/api/file/{path:.+}", handlers.file_write),')
r.write_text(t, encoding="utf-8", newline="\n")
print("ok")
