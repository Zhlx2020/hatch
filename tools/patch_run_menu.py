import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

h = root / "src/oslab/web/handlers.py"
s = h.read_text(encoding="utf-8")
s = s.replace('''async def settings_get(request):
    return web.json_response(settings.load())''',
'''async def settings_get(request):
    data = await asyncio.to_thread(settings.load)
    data["profiles"] = settings.catalogue()
    data["screen"] = settings.screen_of(data["qemu"]["profile"])
    return web.json_response(data)''')
s = s.replace('''    else:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(data)''', '''    else:
        return web.json_response({"error": str(exc)}, status=400)
    out = dict(data)
    out["profiles"] = settings.catalogue()
    out["screen"] = settings.screen_of(data["qemu"]["profile"])
    return web.json_response(out)''')
h.write_text(s, encoding="utf-8", newline="\n")

i = root / "src/oslab/assets/ui/index.html"
t = i.read_text(encoding="utf-8")
t = t.replace('<button id="run">运行</button>',
'''<div id="run-group">
      <button id="run">运行</button>
      <button id="run-more" title="更多启动方式">▾</button>
      <div id="run-menu">
        <button data-act="run">构建并运行</button>
        <button data-act="build">只构建</button>
        <button data-act="reset">软复位（回复位向量）</button>
        <button data-act="reboot">重新构建并启动</button>
        <button data-act="settings">启动设置…</button>
      </div>
    </div>''')
i.write_text(t, encoding="utf-8", newline="\n")
print("ok")
