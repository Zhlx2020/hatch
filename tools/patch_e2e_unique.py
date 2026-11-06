import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tests/e2e/selftest.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    'results = []',
    'STAMP = "e2e%d" % int(time.time())\nresults = []',
)
s = s.replace(
    '''        # 工作区树 ------------------------------------------------------
        status, nodes = await get(session, "/api/tree")''',
    '''        # 工作区树 ------------------------------------------------------
        status, nodes = await get(session, "/api/tree")''',
)
s = s.replace('{"path": "e2e", "kind": "dir"}', '{"path": STAMP, "kind": "dir"}')
s = s.replace('{"path": "e2e/t.asm", "kind": "file"}', '{"path": STAMP + "/t.asm", "kind": "file"}')
s = s.replace('find(nodes, "e2e/t.asm")', 'find(nodes, STAMP + "/t.asm")')
s = s.replace('{"path": "e2e/t.asm", "name": "u.asm"}', '{"path": STAMP + "/t.asm", "name": "u.asm"}')
s = s.replace('out.get("path") == "e2e/u.asm"', 'out.get("path") == STAMP + "/u.asm"')
s = s.replace('{"path": STAMP + "/t.asm", "name": "u.asm"}', '{"path": STAMP + "/t.asm", "name": "u.asm"}')
s = s.replace('{"path": "e2e/u.asm", "dir": ""}', '{"path": STAMP + "/u.asm", "dir": ""}')
s = s.replace('out.get("path") == "u.asm"', 'out.get("path") == STAMP + "-u.asm"')
s = s.replace('"/api/file/e2e/u.asm"', '"/api/file/" + STAMP + "/u.asm"')
s = s.replace('{"path": "../escape.asm", "kind": "file"}', '{"path": "../escape.asm", "kind": "file"}')
s = s.replace('await post(session, "/api/run", {"name": "shell.asm"})',
              'await post(session, "/api/run", {"name": "serial.asm"})')
s = s.replace('''        async with session.delete(BASE + "/api/node?path=u.asm") as resp:
            check("删除移动到根的文件", resp.status == 200)
        async with session.delete(BASE + "/api/node?path=e2e") as resp:
            check("删除目录", resp.status == 200)''',
              '''        async with session.delete(BASE + "/api/node?path=" + STAMP + "-u.asm") as resp:
            check("删除移动到根的文件", resp.status == 200)
        async with session.delete(BASE + "/api/node?path=" + STAMP) as resp:
            check("删除目录", resp.status == 200)''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
