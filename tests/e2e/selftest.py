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
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print("%-34s %s%s" % (name, "PASS" if ok else "FAIL", " " + detail if detail else ""))


async def post(session, path, body=None):
    async with session.post(BASE + path, json=body or {}) as resp:
        return resp.status, await resp.json()


async def get(session, path):
    async with session.get(BASE + path) as resp:
        return resp.status, await resp.json()


async def main():
    async with aiohttp.ClientSession() as session:
        try:
            await get(session, "/api/state")
        except aiohttp.ClientError:
            check("服务可连接", False, "先运行 python -m oslab --serve")
            return

        status, files = await get(session, "/api/files")
        check("文件列表可读", status == 200 and isinstance(files, list))

        # 屏幕：连上 ws 应立刻收到 RFB 前缀
        async with session.ws_connect(BASE + "/ws/screen") as ws:
            first = await asyncio.wait_for(ws.receive_bytes(), 5)
            check("屏幕握手有输出", first[:4] == b"RFB ")

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
        _, snap = await get(session, "/api/state")
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

        status, _ = await post(session, "/api/step")
        check("单步可用", status == 200)

        _, snap = await get(session, "/api/state")
        target = snap.get("eip")
        status, out = await post(session, "/api/bp", {"addr": target})
        check("设断点", status == 200, str(out))
        status, out = await post(session, "/api/cont")
        check("继续可用", status == 200, str(out))

        _, text = await get(session, "/api/serial")
        check("串口有输出", "KEYBOARD" in text.get("text", ""))

        await post(session, "/api/run", {"name": "shell.asm"})
        _, again = await get(session, "/api/state")
        check("再次运行后仍是运行中", again.get("state") == "running")

    failures = results.count(False)
    print("\n%d/%d 通过" % (len(results) - failures, len(results)))
    sys.exit(failures)


asyncio.run(main())
