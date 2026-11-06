"""Bochs rfb frame source.

Bochs speaks 8bpp 3-3-2, ignores SetPixelFormat and paints a header plus status
bar we do not want. We keep one persistent rfb connection, translate to 32bpp
RGBA with the crop applied, and fan the result out to every viewer, so page
reloads never churn Bochs' single client slot.
"""
import asyncio
import struct

from .. import config
from . import codec

CLIENT_INPUT = (b"\x03", b"\x04", b"\x05", b"\x06")


async def _readn(reader, n):
    return await reader.readexactly(n)


class RfbSource:
    name = "rfb"

    def __init__(self, host=config.HOST, port=config.RFB_PORT):
        self.host = host
        self.port = port
        self.width = 0
        self.height = 0
        self.viewers = set()
        self._task = None
        self._writer = None
        self.online = False

    # lifecycle ------------------------------------------------------
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
            await asyncio.sleep(0.5)

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
        self._writer.write(b"RFB 003.003\n")
        await _readn(reader, 4)
        self._writer.write(b"\x01")
        head = await _readn(reader, 24)
        self.width, self.height = struct.unpack(">HH", head[:4])
        nlen = struct.unpack(">I", head[20:24])[0]
        if nlen:
            await _readn(reader, nlen)
        self._writer.write(struct.pack(">BBH", 2, 0, 0))
        await self._writer.drain()

    # pump -----------------------------------------------------------
    async def _pump(self, reader):
        while True:
            self._ask()
            head = await _readn(reader, 4)
            nrects = struct.unpack(">H", head[2:4])[0]
            for _ in range(nrects):
                hdr = await _readn(reader, 12)
                x, y, w, h, enc = struct.unpack(">HHHHi", hdr)
                data = await _readn(reader, w * h) if enc == 0 else b""
                self._broadcast(x, y, w, h, data)
            await asyncio.sleep(config.FRAME_MS / 1000.0)

    def _ask(self):
        if not self._writer:
            return
        view_h = max(1, self.height - config.HEADERBAR - config.STATUSBAR)
        msg = struct.pack(">BBHHHH", 3, 0, 0, 0, view_h, self.width)
        try:
            self._writer.write(msg)
        except OSError:
            pass

    def _broadcast(self, x, y, w, h, data):
        if not data or not self.viewers:
            return
        top = max(0, y - config.HEADERBAR)
        bottom = min(self.height - config.STATUSBAR, y + h) - config.HEADERBAR
        if bottom <= top:
            return
        skip = (top + config.HEADERBAR - y) * w
        rows = data[skip:skip + (bottom - top) * w]
        message = (struct.pack(">BBH", 0, 0, 1) +
                   struct.pack(">HHHHi", x, top, w, bottom - top, 0) +
                   codec.expand(rows))
        for ws in list(self.viewers):
            self._send(ws, message)

    @staticmethod
    def _send(ws, message):
        task = asyncio.ensure_future(ws.send_bytes(message))
        task.add_done_callback(lambda t: t.exception())

    # viewers --------------------------------------------------------
    async def _wait_online(self, timeout=6.0):
        for _ in range(int(timeout / 0.05)):
            if self.online and self.width:
                return True
            await asyncio.sleep(0.05)
        return False

    async def attach(self, ws):
        self.start()
        await self._wait_online()
        await ws.send_bytes(b"RFB 003.008\n")
        await ws.send_bytes(b"\x01\x01")
        await ws.send_bytes(b"\x00\x00\x00\x00")
        view_h = max(1, self.height - config.HEADERBAR - config.STATUSBAR)
        pf = struct.pack(">BBBBHHHBBBBBB", 32, 24, 0, 1, 255, 255, 255, 0, 8, 16, 0, 0, 0)
        await ws.send_bytes(struct.pack(">HH", self.width, view_h) + pf +
                            struct.pack(">I", 3) + b"VGA")
        self.viewers.add(ws)
        try:
            while True:
                msg = await ws.receive()
                if msg.type.name == "CLOSE":
                    return
                if msg.type.name == "BINARY" and msg.data[:1] in CLIENT_INPUT:
                    if self._writer:
                        try:
                            self._writer.write(msg.data)
                        except OSError:
                            pass
        finally:
            self.viewers.discard(ws)
