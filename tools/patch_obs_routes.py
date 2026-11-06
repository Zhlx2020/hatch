import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "web/handlers.py"
s = p.read_text(encoding="utf-8")

anchor = "# control -------------------------------------------------------------"
addition = '''# observation ----------------------------------------------------------
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


async def disasm(request):
    body = await request.json()
    addr = int(str(body.get("addr", "0")), 16)
    count = int(body.get("count", 32))
    try:
        out = await asyncio.to_thread(session().disasm_rows, addr, count)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(out)


'''
s = s.replace(anchor, addition + anchor)
p.write_text(s, encoding="utf-8", newline="\n")

r = root / "web/routes.py"
t = r.read_text(encoding="utf-8")
t = t.replace('    ("POST", "/api/mem", handlers.mem),\n',
              '    ("GET", "/api/regs", handlers.regs),\n'
              '    ("POST", "/api/reg", handlers.reg_set),\n'
              '    ("POST", "/api/mem", handlers.mem),\n'
              '    ("POST", "/api/disasm", handlers.disasm),\n')
r.write_text(t, encoding="utf-8", newline="\n")
print("ok")
