"""QEMU VNC frame source.

QEMU negotiates 32bpp BGRX natively and paints no chrome, so this source is a
straight pass-through: one persistent client, frames broadcast to viewers.
"""
import asyncio
import struct

from .. import config

PIXEL_FORMAT = struct.pack(">BBBBHHHBBBBBB", 32, 24, 0, 1, 255, 255, 255, 16, 8, 0, 0, 0, 0)


async def _readn(reader, n):
    return await reader.readexactly(n)


class VncSource:
    name = "vnc"

    def __init__(self, host=config.HOST, port=config.RFB_PORT):
        self.host = host
        self.port = port
        self.width = 0
        self.height = 0
        self.viewers = set()
        self._task = None
        self._writer = None
        self.online = False

    def start(self, loop=None):
        if self._task is None or self._task.done():
            loop = loop or asyncio.get_event_loop_policy().get_event_loop()
            self._task = loop.create_task(self._supervise())

    async def stop(self):
        task, self._task = self._task, None
        if task:
            task.cancel()

    async def _supervise(self):
        while True:
            try:
                await self._session()
            except asyncio.CancelledError:
                raise
            except (ConnectionError, asyncio.IncompleteReadError, OSError):
                pass
            finally:
                self.online = False
                self._writer = None
            await asyncio.sleep(0.4)

    async def _session(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        self._writer = writer
        try:
            await self._handshake(reader)
            self.online = True
            pump = asyncio.create_task(self._pump(reader))
            try:
                await pump
            finally:
                pump.cancel()
        finally:
            writer.close()

    async def _handshake(self, reader):
        await _readn(reader, 12)
        self._writer.write(b"RFB 003.008\n")
        count = (await _readn(reader, 1))[0]
        types = await _readn(reader, count)
        self._writer.write(bytes([1 if 1 in types else types[0]]))
        await _readn(reader, 4)
        self._writer.write(b"\x01")
        head = await _readn(reader, 24)
        self.width, self.height = struct.unpack(">HH", head[:4])
        nlen = struct.unpack(">I", head[20:24])[0]
        if nlen:
            await _readn(reader, nlen)
        self._writer.write(struct.pack(">Bxxx", 0) + PIXEL_FORMAT)
        self._writer.write(struct.pack(">BxH", 2, 2) +
                           struct.pack(">i", 0) + struct.pack(">i", -223))
        await self._writer.drain()

    async def _pump(self, reader):
        while True:
            head = await _readn(reader, 4)
            if head[0] != 0:
                await self._skip(reader, head)
                continue
            rects = struct.unpack(">H", head[2:4])[0]
            parts = [head]
            for _ in range(rects):
                hdr = await _readn(reader, 12)
                x, y, w, h, enc = struct.unpack(">HHHHi", hdr)
                parts.append(hdr)
                if enc == -223:
                    self.width, self.height = w, h
                elif enc == 0:
                    parts.append(await _readn(reader, w * h * 4))
            self._broadcast(b"".join(parts))

    async def _skip(self, reader, head):
        if head[0] == 3:
            rest = await _readn(reader, 7)
            length = struct.unpack(">I", rest[3:7])[0]
            if length:
                await _readn(reader, length)

    def _broadcast(self, message):
        for ws in list(self.viewers):
            task = asyncio.ensure_future(ws.send_bytes(message))
            task.add_done_callback(lambda t: t.exception())

    async def attach(self, ws):
        self.start()
        for _ in range(120):
            if self.online and self.width:
                break
            await asyncio.sleep(0.05)
        await ws.send_bytes(b"RFB 003.008\n")
        await ws.send_bytes(b"\x01\x01")
        await ws.send_bytes(b"\x00\x00\x00\x00")
        await ws.send_bytes(struct.pack(">HH", self.width, self.height) + PIXEL_FORMAT +
                            struct.pack(">I", 3) + b"QEM")
        self.viewers.add(ws)
        try:
            while True:
                msg = await ws.receive()
                if msg.type.name == "CLOSE":
                    return
                if msg.type.name == "BINARY" and msg.data[:1] in (b"\x03", b"\x04", b"\x05", b"\x06"):
                    if self._writer:
                        try:
                            with open(config.RUN_DIR + "/ws.log", "a") as fh:
                                fh.write("%d %s\n" % (len(msg.data),
                                                      " ".join("%02x" % b for b in msg.data)))
                            self._writer.write(msg.data)
                        except OSError:
                            pass
        finally:
            self.viewers.discard(ws)
