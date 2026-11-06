import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tests/e2e/selftest.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''        # 清理 ----------------------------------------------------------''',
'''        # 本轮新增：行断点、模板、配置 ---------------------------------
        status, files = await get(session, "/api/templates")
        check("模板列表", status == 200 and {item["name"] for item in files}
              >= {"asm-hello", "c-hello"}, str(files)[:80])

        status, made = await post(session, "/api/template",
                                  {"name": "c-hello", "dir": STAMP + "-c"})
        check("从模板建工程", status == 200 and made.get("entry", "").endswith("kmain.c"),
              str(made)[:80])

        status, ran = await post(session, "/api/run",
                                 {"name": STAMP + "-c/src/kmain.c", "lines": [9]})
        check("C 工程能构建启动", status == 200, str(ran)[:80])

        await asyncio.sleep(0.6)
        _, c_state = await get(session, "/api/state")
        check("C 行断点会停住", c_state.get("state") == "stopped"
              and c_state.get("line") == 9 and c_state.get("bps"),
              str(c_state)[:100])

        status, mapped = await get(session, "/api/line?path=" + STAMP + "-c/src/kmain.c&line=9")
        check("行号能查地址", status == 200 and mapped.get("addr", "").startswith("0001"),
              str(mapped))
        status, missing = await get(session, "/api/line?path=" + STAMP + "-c/src/none.c&line=3")
        check("查不到时给原因", status == 200 and not missing.get("addr")
              and missing.get("reason"), str(missing))

        status, conf = await get(session, "/api/settings")
        check("读到配置", status == 200 and conf["qemu"]["memory"] >= 4, str(conf)[:80])
        status, saved = await put(session, "/api/settings",
                                  {"qemu": {"memory": 40, "extra": ["-no-reboot"]}})
        check("配置可保存", status == 200 and saved["qemu"]["memory"] == 40, str(saved)[:80])
        status, refused = await put(session, "/api/settings",
                                    {"qemu": {"extra": ["-m", "9"]}})
        check("托管参数会拒绝", status == 400 and "界面管理" in (refused.get("error") or ""),
              str(refused))
        status, restored = await put(session, "/api/settings",
                                     {"qemu": {"memory": 32, "extra": []}})
        check("配置可还原", status == 200 and restored["qemu"]["memory"] == 32)

        # 清理 ----------------------------------------------------------''')

s = s.replace('''        async with session.delete(BASE + "/api/node?path=" + STAMP) as resp:
            check("删除目录", resp.status == 200)''',
'''        async with session.delete(BASE + "/api/node?path=" + STAMP) as resp:
            check("删除目录", resp.status == 200)
        async with session.delete(BASE + "/api/node?path=" + STAMP + "-c") as resp:
            check("删除模板工程", resp.status == 200)''')
p.write_text(s, encoding="utf-8", newline="\n")
print("put" in s)
