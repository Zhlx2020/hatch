import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tests/e2e/selftest.py"
s = p.read_text(encoding="utf-8")

anchor = '''        check("反汇编按地址取", status == 200 and out["rows"], str(out)[:120])'''
extra = anchor + '''

        status, out = await post(session, "/api/disasm",
                                 {"addr": "%08x" % eip, "count": 4})
        intel_text = " ".join(row["text"] for row in out["rows"])
        check("反汇编默认 intel", status == 200 and "%eax" not in intel_text, intel_text)

        status, out = await post(session, "/api/disasm",
                                 {"addr": "%08x" % eip, "count": 4, "syntax": "att"})
        att_text = " ".join(row["text"] for row in out["rows"])
        check("反汇编可切 att", status == 200 and "%" in att_text, att_text)'''
s = s.replace(anchor, extra)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
