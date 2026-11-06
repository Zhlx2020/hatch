import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/web/handlers.py"
s = p.read_text(encoding="utf-8")

if "async def settings_get" not in s:
    s = s.replace("async def run(request):", '''async def settings_get(request):
    return web.json_response(services.settings.load())


async def settings_put(request):
    body = await request.json()
    try:
        data = services.settings.save(body)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(data)


async def run(request):''')
p.write_text(s, encoding="utf-8", newline="\n")

r = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/web/routes.py"
t = r.read_text(encoding="utf-8")
t = t.replace('    ("POST", "/api/run", handlers.run),',
              '    ("GET", "/api/settings", handlers.settings_get),\n'
              '    ("PUT", "/api/settings", handlers.settings_put),\n'
              '    ("POST", "/api/run", handlers.run),')
r.write_text(t, encoding="utf-8", newline="\n")
print("ok")
