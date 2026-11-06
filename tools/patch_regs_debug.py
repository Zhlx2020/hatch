import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/web/handlers.py"
s = p.read_text(encoding="utf-8")
s = s.replace('''async def regs(_request):
    try:
        return web.json_response(await asyncio.to_thread(session().reg_detail))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)''',
'''async def regs(_request):
    import traceback

    try:
        return web.json_response(await asyncio.to_thread(session().reg_detail))
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except Exception as exc:  # TEMP
        return web.json_response({"crash": repr(exc),
                                  "trace": traceback.format_exc()}, status=500)''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
