import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tests/e2e/selftest.py"
s = p.read_text(encoding="utf-8")

anchor = '''        status, _ = await post(session, "/api/step")
        check("单步可用", status == 200)'''
extra = '''        status, lint = await post(session, "/api/check",
                                 {"path": "x.asm", "text": "bits 16\\norg 0x7c00\\nmov ax,\\n"})
        check("编辑器诊断报行号", status == 200 and lint["errors"][0]["line"] == 3, str(lint))

        status, lint = await post(session, "/api/check",
                                 {"path": "x.asm",
                                  "text": "bits 16\\norg 0x7c00\\nhlt\\ntimes 510-($-$$) db 0\\ndw 0xaa55\\n"})
        check("编辑器诊断放过正确代码", status == 200 and lint["ok"] is True, str(lint))

        status, _ = await post(session, "/api/step")
        check("单步可用", status == 200)'''
s = s.replace(anchor, extra)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
