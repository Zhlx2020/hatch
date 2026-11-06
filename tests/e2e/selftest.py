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


async def get(session, path):
    async with session.get(BASE + path) as resp:
        if resp.content_type == "application/json":
            return resp.status, await resp.json()
        return resp.status, {}


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
            first = await asyncio.wait_for(ws.receive_bytes(), 5)
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

        # 清理 ----------------------------------------------------------
        async with session.delete(BASE + "/api/node?path=" + STAMP + "-u.asm") as resp:
            check("删除移动到根的文件", resp.status == 200)
        async with session.delete(BASE + "/api/node?path=" + STAMP) as resp:
            check("删除目录", resp.status == 200)

    failures = results.count(False)
    print("\n%d/%d 通过" % (len(results) - failures, len(results)))
    sys.exit(failures)


asyncio.run(main())
