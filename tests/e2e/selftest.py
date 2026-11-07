"""End-to-end acceptance run against a live oslab server.

    python -m oslab --serve          (in another shell)
    python tests/e2e/selftest.py

Every step prints PASS/FAIL; the exit code is the number of failures.
"""
import asyncio
import sys
import time

import aiohttp

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8799
BASE = "http://127.0.0.1:%d" % PORT
STAMP = "e2e%d" % int(time.time())
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print("%-34s %s%s" % (name, "PASS" if ok else "FAIL", " " + detail if detail else ""))


async def post(session, path, body=None):
    async with session.post(BASE + path, json=body or {}) as resp:
        return resp.status, await resp.json()


async def delete(session, path, body=None):
    async with session.delete(BASE + path, json=body or {}) as resp:
        return resp.status, await resp.json()


async def get(session, path):
    async with session.get(BASE + path) as resp:
        if resp.content_type == "application/json":
            return resp.status, await resp.json()
        return resp.status, {}


async def put(session, path, body):
    async with session.put(BASE + path, json=body) as resp:
        return resp.status, await resp.json()


def find(nodes, path):
    for node in nodes:
        if node["path"] == path:
            return node
        if node["kind"] == "dir":
            hit = find(node["children"], path)
            if hit:
                return hit
    return None


async def main():
    async with aiohttp.ClientSession() as session:
        try:
            await get(session, "/api/state")
        except aiohttp.ClientError:
            check("服务可连接", False, "先运行 python -m oslab --serve")
            return

        # 工作区树 ------------------------------------------------------
        status, nodes = await get(session, "/api/tree")
        check("工作区树可读", status == 200 and isinstance(nodes, list))

        status, out = await post(session, "/api/node", {"path": STAMP, "kind": "dir"})
        check("新建目录", status == 200, str(out))
        status, out = await post(session, "/api/node", {"path": STAMP + "/t.asm", "kind": "file"})
        check("新建文件", status == 200, str(out))

        _, nodes = await get(session, "/api/tree")
        check("新节点出现在树里", find(nodes, STAMP + "/t.asm") is not None)

        status, out = await post(session, "/api/node/rename",
                                 {"path": STAMP + "/t.asm", "name": STAMP + "-u.asm"})
        check("重命名", status == 200 and out.get("path") == STAMP + "/" + STAMP + "-u.asm", str(out))

        status, out = await post(session, "/api/node", {"path": "e2e/bad name.asm",
                                                        "kind": "file"})
        check("非法名字被拒", status == 400)

        status, out = await post(session, "/api/node/move", {"path": STAMP + "/" + STAMP + "-u.asm", "dir": ""})
        check("移动到根", status == 200 and out.get("path") == STAMP + "-u.asm", str(out))

        status, out = await post(session, "/api/node", {"path": "../escape.asm", "kind": "file"})
        check("路径穿越被拒", status == 400)

        status, _ = await get(session, "/api/file/" + STAMP + "/" + STAMP + "-u.asm")
        check("改名后旧路径消失", status == 404)

        # 屏幕 ----------------------------------------------------------
        async with session.ws_connect(BASE + "/ws/screen") as ws:
            # 第一次接手画面要等客户机把 VNC 服务开起来，慢机器上要十几秒
            first = await asyncio.wait_for(ws.receive_bytes(), 25)
            check("屏幕握手有输出", first[:4] == b"RFB ")

        # 运行与调试 ----------------------------------------------------
        status, out = await post(session, "/api/run", {"name": "keyboard.asm"})
        check("运行键值样例", status == 200 and out.get("state") == "running", str(out))

        deadline = time.time() + 5
        running = False
        while time.time() < deadline:
            _, snap = await get(session, "/api/state")
            if snap.get("state") == "running":
                running = True
                break
            await asyncio.sleep(0.2)
        check("状态进入运行中", running)

        started = time.time()
        await get(session, "/api/state")
        elapsed = time.time() - started
        check("运行中取状态 <300ms", elapsed < 0.3, "%.0fms" % (elapsed * 1000))

        status, out = await post(session, "/api/pause")
        check("暂停可用", status == 200, str(out))

        _, snap = await get(session, "/api/state")
        eip = snap.get("eip", "")
        check("暂停后能读 eip", snap.get("state") == "stopped" and len(eip) == 8, eip)
        check("暂停后能读寄存器", "eax" in (snap.get("regs") or ""))
        check("暂停后能读反汇编", bool(snap.get("disasm")))
        check("暂停后能读内存", bool(snap.get("mem")))

        status, regs = await get(session, "/api/regs")
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
        intel_text = " ".join(row["text"] for row in (dis.get("rows") or []))
        check("反汇编默认 intel", "%" not in intel_text, intel_text[:60])

        status, dis = await post(session, "/api/disasm",
                                 {"addr": "7c00", "count": 8, "syntax": "att"})
        att_text = " ".join(row["text"] for row in (dis.get("rows") or []))
        check("反汇编可切 att", status == 200 and "$" in att_text, att_text[:60])
        check("十六位反汇编不错位", "<.data>" not in att_text and "(bad)" not in intel_text,
              att_text[:60])

        status, lint = await post(session, "/api/check",
                                 {"path": "x.asm", "text": "bits 16\norg 0x7c00\nmov ax,\n"})
        check("编辑器诊断报行号", status == 200 and lint["errors"][0]["line"] == 3, str(lint))

        status, lint = await post(session, "/api/check",
                                 {"path": "x.asm",
                                  "text": "bits 16\norg 0x7c00\nhlt\ntimes 510-($-$$) db 0\ndw 0xaa55\n"})
        check("编辑器诊断放过正确代码", status == 200 and lint["ok"] is True, str(lint))

        status, _ = await post(session, "/api/step")
        check("单步可用", status == 200)

        _, snap = await get(session, "/api/state")
        status, out = await post(session, "/api/bp", {"addr": snap.get("eip")})
        check("设断点", status == 200, str(out))
        status, out = await post(session, "/api/cont")
        check("继续可用", status == 200, str(out))

        _, text = await get(session, "/api/serial")
        check("串口有输出", "KEYBOARD" in text.get("text", ""))

        await post(session, "/api/run", {"name": "serial.asm"})
        _, again = await get(session, "/api/state")
        check("再次运行后仍是运行中", again.get("state") == "running")

        status, bad = await post(session, "/api/run", {"name": "boot/banner.inc"})
        _, failed = await get(session, "/api/state")
        check("装了不能跑的文件会说清原因",
              status == 400 and "不能运行" in (bad.get("error") or "")
              and failed.get("state") == "faulted"
              and "不能运行" in (failed.get("error") or ""), str(failed)[:80])

        # 本轮新增：行断点、模板、配置 ---------------------------------
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

        # 自备引导链与自己的构建命令 -------------------------------------
        status, chain = await post(session, "/api/template",
                                   {"name": "chain", "dir": STAMP + "-ch"})
        check("建两级引导工程", status == 200, str(chain)[:80])
        status, chain_run = await post(session, "/api/run", {"name": STAMP + "-ch/boot.asm"})
        check("两级引导能起来", status == 200, str(chain_run)[:80])
        await asyncio.sleep(0.6)
        await post(session, "/api/pause")
        _, ch_state = await get(session, "/api/state")
        check("第二级跑在 0x9000", ch_state.get("eip", "").startswith("00009"), str(ch_state)[:80])

        async with session.put(BASE + "/api/file/" + STAMP + "-ch/oslab.toml",
                               json={"text": 'kind = "asm"\nentry = "boot.asm"\n'
                                             'boot = "boot.asm"\n'
                                             'stages = [{ path = "boot.asm" }]\n'}) as resp:
            check("写坏清单", resp.status == 200)
        status, conflict = await post(session, "/api/run", {"name": STAMP + "-ch/boot.asm"})
        check("boot 与 stages 同写被拒", status == 400
              and "只能写一个" in (conflict.get("error") or ""), str(conflict)[:80])

        status, scripted = await post(session, "/api/run", {"name": "scripted/boot.asm"})
        check("自己的构建命令能跑", status == 200, str(scripted)[:80])

        status, kept = await put(session, "/api/settings",
                                 {"qemu": {"memory": 16,
                                           "disks": [{"path": "root.img",
                                                      "iface": "floppy", "index": 1}]}})
        check("内存和附加盘存得住", status == 200 and kept["qemu"]["memory"] == 16
              and kept["qemu"]["disks"][0]["index"] == 1, str(kept)[:100])
        status, gone = await post(session, "/api/run", {"name": "boot/main.asm"})
        check("盘不在时说清是哪个", status == 400 and "附加盘不存在" in (gone.get("error") or ""),
              str(gone)[:80])
        await put(session, "/api/settings", {"qemu": {"memory": 0, "disks": []}})
        # 回到 C 工程，后面的布局 / 行号检查才有东西看
        await post(session, "/api/run", {"name": STAMP + "-c/src/kmain.c", "lines": [9]})
        await asyncio.sleep(1.0)

        # 磁盘布局与 ELF 结构 -------------------------------------------
        status, layout = await get(session, "/api/disk")
        kinds = [row.get("kind") for row in layout.get("regions") or []]
        check("磁盘布局分段", status == 200 and "boot" in kinds and "code" in kinds
              and layout.get("size") == 1474560, str(kinds))
        fields = [row.get("k") for row in (layout["regions"][0].get("fields") or [])]
        check("引导扇区逐项列出", "510-511 字节" in fields, str(fields))
        check("行号落到镜像偏移", any(mark.get("offset") for mark in layout.get("marks") or []),
              str(layout.get("marks"))[:80])
        status, bad = await get(session, "/api/disk")
        check("布局带签名检查结论", status == 200 and isinstance(layout.get("warnings"), list))

        status, jump = await post(session, "/api/declare",
                                  {"path": STAMP + "-c/src/kmain.c", "word": "screen_clear"})
        where = [(row["file"], row["line"]) for row in jump.get("hits") or []]
        check("函数能跳声明", status == 200 and where
              and where[0][0].endswith("screen.c"), str(where)[:80])
        check("定义排在声明前面", (jump["hits"][0].get("def") if where else False) is True)
        status, label = await post(session, "/api/declare",
                                   {"path": "boot/main.asm", "word": "start"})
        check("汇编标签能跳", status == 200 and (label.get("hits") or [{}])[0].get("line") == 6,
              str(label)[:80])
        status, none = await post(session, "/api/declare",
                                  {"path": "boot/main.asm", "word": "mov"})
        check("跳不到的给空表", status == 200 and none.get("hits") == [])

        await delete(session, "/api/bookmarks", {"file": "boot/main.asm"})
        status, marked = await post(session, "/api/bookmarks",
                                    {"file": "boot/main.asm", "line": 3, "text": "jmp start"})
        check("能加书签", status == 200 and marked.get("on") is True
              and marked["marks"][0]["line"] == 3, str(marked)[:80])
        status, listed = await get(session, "/api/bookmarks")
        mine = [row for row in listed.get("marks") or [] if row["file"] == "boot/main.asm"]
        check("书签能列出来", status == 200 and len(mine) == 1, str(listed)[:80])
        status, again = await post(session, "/api/bookmarks",
                                   {"file": "boot/main.asm", "line": 3})
        check("再点一次就取消", status == 200 and again.get("on") is False
              and not [row for row in again.get("marks") or []
                       if row["file"] == "boot/main.asm"])
        await post(session, "/api/bookmarks", {"file": "boot/main.asm", "line": 3})
        status, dropped = await delete(session, "/api/bookmarks",
                                       {"file": "boot/main.asm", "line": 3})
        check("书签能删", status == 200
              and not [row for row in dropped.get("marks") or []
                       if row["file"] == "boot/main.asm"], str(dropped)[:80])

        status, info = await get(session, "/api/elf")
        names = [row.get("name") for row in info.get("sections") or []]
        check("ELF 能读节表", status == 200 and ".text" in names
              and info.get("machine") == "i386", str(names)[:80])
        check("ELF 入口在代码里", info.get("entry") == 0x10000, str(info.get("entry")))
        check("ELF 有符号", (info.get("symbol_total") or 0) >= 1,
              str(info.get("symbol_total")))

        status, conf = await get(session, "/api/settings")
        check("读得到模板清单", status == 200 and len(conf.get("profiles") or []) >= 5
              and conf["qemu"]["profile"], str(conf)[:80])
        status, saved = await put(session, "/api/settings",
                                  {"qemu": {"profile": "cold", "extra": ["-no-reboot"]}})
        check("模板可保存", status == 200 and saved["qemu"]["profile"] == "cold", str(saved)[:80])
        status, refused = await put(session, "/api/settings",
                                    {"qemu": {"extra": ["-m", "9"]}})
        check("模板占用的参数会拒绝", status == 400 and "模板管理" in (refused.get("error") or ""),
              str(refused))
        status, denied = await put(session, "/api/settings", {"qemu": {"profile": "nope"}})
        check("不存在的模板会拒绝", status == 400 and "没有这个模板" in (denied.get("error") or ""))
        status, restored = await put(session, "/api/settings",
                                     {"qemu": {"profile": "floppy", "extra": []}})
        check("配置可还原", status == 200 and restored["qemu"]["profile"] == "floppy")

        # 启动方式：某一项单独改，别的项不动 -------------------------------
        status, one = await put(session, "/api/settings",
                                {"run": {"label": "调试", "action": "build"}})
        check("按钮文字可单独改", status == 200 and one["run"]["label"] == "调试"
              and one["run"]["action"] == "build", str(one)[:80])
        status, kept = await put(session, "/api/settings", {"run": {"pause_at_entry": False}})
        check("改一项不冲掉另一项", status == 200 and kept["run"]["label"] == "调试"
              and kept["run"]["pause_at_entry"] is False, str(kept)[:80])
        status, bad = await put(session, "/api/settings", {"run": {"action": "delete"}})
        check("按钮动作只能是两种", status == 400 and "run" in (bad.get("error") or ""), str(bad))
        status, back = await put(session, "/api/settings",
                                 {"run": {"label": "运行", "action": "run",
                                          "pause_at_entry": True}})
        check("改回运行", status == 200 and back["run"]["action"] == "run", str(back)[:80])

        # 清理 ----------------------------------------------------------
        async with session.delete(BASE + "/api/node?path=" + STAMP + "-u.asm") as resp:
            check("删除移动到根的文件", resp.status == 200)
        async with session.delete(BASE + "/api/node?path=" + STAMP) as resp:
            check("删除目录", resp.status == 200)
        async with session.delete(BASE + "/api/node?path=" + STAMP + "-c") as resp:
            check("删除模板工程", resp.status == 200)
        async with session.delete(BASE + "/api/node?path=" + STAMP + "-ch") as resp:
            check("删除引导链工程", resp.status == 200)

    failures = results.count(False)
    print("\n%d/%d 通过" % (len(results) - failures, len(results)))
    sys.exit(failures)


asyncio.run(main())
