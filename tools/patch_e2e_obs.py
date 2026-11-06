import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tests/e2e/selftest.py"
s = p.read_text(encoding="utf-8")

anchor = '''        status, _ = await post(session, "/api/step")
        check("单步可用", status == 200)'''
extra = '''        status, regs = await get(session, "/api/regs")
        check("寄存器面板数据", status == 200 and isinstance(regs.get("regs"), dict))

        status, out = await post(session, "/api/reg", {"name": "eax", "value": "0x1234"})
        check("写回寄存器", status == 200 and out.get("value") == "00001234", str(out))
        _, again_regs = await get(session, "/api/regs")
        check("写回生效", again_regs.get("regs", {}).get("eax") == 0x1234)

        status, mem = await post(session, "/api/mem", {"addr": "7c00", "count": 64})
        check("内存分页读取", status == 200 and len(mem.get("rows", [])) == 4, str(out))

        status, dis = await post(session, "/api/disasm", {"addr": "7c00", "count": 8})
        check("反汇编按地址取", status == 200 and dis.get("rows")
              and dis["rows"][0]["text"] != "", str(dis)[:60])

        status, _ = await post(session, "/api/step")
        check("单步可用", status == 200)'''
s = s.replace(anchor, extra)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
