import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/web/handlers.py"
s = p.read_text(encoding="utf-8")

s = s.replace("from ..services import checker, settings, workspace",
              "from ..services import checker, settings, templates, workspace")

s = s.replace("async def settings_get(request):", '''async def templates_list(request):
    return web.json_response(templates.entries())


async def templates_apply(request):
    body = await request.json()
    try:
        out = await asyncio.to_thread(templates.apply, body.get("name", ""),
                                      body.get("dir", ""))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(out)


async def settings_get(request):''')
p.write_text(s, encoding="utf-8", newline="\n")

r = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/web/routes.py"
t = r.read_text(encoding="utf-8")
t = t.replace('    ("GET", "/api/settings", handlers.settings_get),',
              '    ("GET", "/api/templates", handlers.templates_list),\n'
              '    ("POST", "/api/template", handlers.templates_apply),\n'
              '    ("GET", "/api/settings", handlers.settings_get),')
r.write_text(t, encoding="utf-8", newline="\n")
print("ok")
