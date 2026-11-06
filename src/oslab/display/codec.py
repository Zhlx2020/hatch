"""Pixel conversion shared by frame sources: Bochs 8bpp 3-3-2 -> RGBA bytes."""
LUT = []
for _v in range(256):
    _r = ((_v >> 5) & 0x7) * 36
    _g = ((_v >> 2) & 0x7) * 36
    _b = (_v & 0x3) * 85
    LUT.append(bytes((_r, _g, _b, 255)))


def expand(rows):
    """8bpp row bytes -> RGBA bytes."""
    return b"".join(map(LUT.__getitem__, rows))
