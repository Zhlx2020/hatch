import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/display/rfb.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    "    def start(self):\n        if self._task is None or self._task.done():\n            self._task = asyncio.get_event_loop().create_task(self._supervise())",
    "    def start(self):\n"
    "        if self._task is None or self._task.done():\n"
    "            self._task = asyncio.get_running_loop().create_task(self._supervise())",
)

s = s.replace(
    "    async def attach(self, ws):\n"
    "        await asyncio.to_thread(self.start) if False else self.start()\n",
    "    async def _wait_online(self, timeout=6.0):\n"
    "        for _ in range(int(timeout / 0.05)):\n"
    "            if self.online and self.width:\n"
    "                return True\n"
    "            await asyncio.sleep(0.05)\n"
    "        return False\n"
    "\n"
    "    async def attach(self, ws):\n"
    "        self.start()\n"
    "        await self._wait_online()\n",
)

p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
