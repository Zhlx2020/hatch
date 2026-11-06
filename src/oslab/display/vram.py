"""Fallback frame source: render text mode straight out of 0xB8000.

Used when rfb is unavailable. Produces the same wire format as the rfb source so
the client needs no second code path.
"""
import asyncio
import struct

from PIL import Image, ImageDraw, ImageFont

from . import codec

COLS, ROWS = 80, 25
CW, CH = 8, 16
BASE = 0xB8000
ATTR = {
    0: (0, 0, 0), 1: (0, 0, 170), 2: (0, 170, 0), 3: (0, 170, 170),
    4: (170, 0, 0), 5: (170, 0, 170), 6: (170, 85, 0), 7: (170, 170, 170),
    8: (85, 85, 85), 9: (85, 85, 255), 10: (85, 255, 85), 11: (85, 255, 255),
    12: (255, 85, 85), 13: (255, 85, 255), 14: (255, 255, 85), 15: (255, 255, 255),
}


def _glyphs():
    font = ImageFont.load_default()
    table = {}
    for code in range(32, 127):
        img = Image.new("1", (CW, CH), 0)
        ImageDraw.Draw(img).text((1, 4), chr(code), fill=1, font=font)
        table[code] = img.tobytes()
    return table


class VramSource:
    name = "vram"

    def __init__(self, backend):
        self.backend = backend
        self.width = COLS * CW
        self.height = ROWS * CH
        self._glyphs = _glyphs()

    async def attach(self, ws):
        await ws.send_bytes(b"RFB 003.008\n")
        await ws.send_bytes(b"\x01\x01")
        await ws.send_bytes(b"\x00\x00\x00\x00")
        pf = struct.pack(">BBBBHHHBBBBBB", 32, 24, 0, 1, 255, 255, 255, 0, 8, 16, 0, 0, 0)
        await ws.send_bytes(struct.pack(">HH", self.width, self.height) + pf +
                            struct.pack(">I", 4) + b"VRAM")
        while True:
            msg = await ws.receive()
            if msg.type.name == "CLOSE":
                return
            if msg.type.name != "BINARY":
                continue
            if msg.data[:1] != b"\x03":
                continue
            frame = await asyncio.to_thread(self._render)
            await ws.send_bytes(struct.pack(">BBH", 0, 0, 1) +
                                struct.pack(">HHHHi", 0, 0, self.width, self.height, 0) +
                                frame)

    def _render(self):
        mem = self.backend.read_mem(BASE, COLS * ROWS * 2)
        buf = bytearray(self.width * self.height * 4)
        stride = self.width * 4
        for cell in range(COLS * ROWS):
            ch = mem[cell * 2]
            attr = mem[cell * 2 + 1] if cell * 2 + 1 < len(mem) else 7
            fg = ATTR[attr & 0x0F]
            bg = ATTR[(attr >> 4) & 0x0F]
            mask = self._glyphs.get(ch, self._glyphs[32])
            ox = (cell % COLS) * CW
            oy = (cell // COLS) * CH
            for y in range(CH):
                row = oy + y
                for x in range(CW):
                    on = mask[y * CW + x]
                    px = fg if on else bg
                    off = row * stride + (ox + x) * 4
                    buf[off:off + 4] = bytes((px[0], px[1], px[2], 255))
        return bytes(buf)
