"""Evaluate a probe expression on the running app page."""
import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request

import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "http://127.0.0.1:8799/"
EXPR = sys.argv[1] if len(sys.argv) > 1 else "document.title"


async def req(ws, i, method, params=None):
    await ws.send(json.dumps({"id": i, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(await asyncio.wait_for(ws.recv(), 20))
        if msg.get("id") == i:
            return msg.get("result", {})


async def main():
    lst = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/list").read())
    page = [t for t in lst if t["type"] == "page"][0]
    ws = await websockets.connect(page["webSocketDebuggerUrl"], max_size=None)
    await req(ws, 1, "Runtime.enable")
    await req(ws, 2, "Page.enable")
    await req(ws, 3, "Runtime.consoleAPICalled")
    await req(ws, 4, "Page.navigate", {"url": URL})
    await asyncio.sleep(4)
    for expr in EXPR.split(";;"):
        await asyncio.sleep(1.5)
        res = await req(ws, 900, "Runtime.evaluate",
                        {"expression": expr, "returnByValue": True, "awaitPromise": True})
        print("->", json.dumps(res.get("result", {}), ensure_ascii=False)[:400])
    await ws.close()


prof = os.path.join(os.environ["TEMP"], "chprof_probe")
chrome = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                           "--user-data-dir=" + prof, "--remote-debugging-port=9222",
                           "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3.0)
try:
    asyncio.run(main())
finally:
    chrome.kill()
