import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/web/handlers.py"
s = p.read_text(encoding="utf-8")

anchor = '''async def disasm(request):'''
new = '''async def line(request):
    """Address of a source line in the last build; 0 when unmapped."""
    path = request.query.get("path", "")
    line = int(request.query.get("line", "0") or 0)
    current = session()
    addr = current.line_addr(path, line)
    reason = "" if addr else "还没构建过这个文件，或者这行没有代码"
    return web.json_response({"addr": "%08x" % addr if addr else "", "reason": reason})


async def disasm(request):'''
s = s.replace(anchor, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")

r = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/web/routes.py"
print(r.read_text(encoding="utf-8")[:1200])
