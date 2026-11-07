"""mkroot.py —— 造一张 0.11 的根盘（minix v1.0），把 sh 和 /etc/rc 放进去。

0.11 要的根盘必须带一个 minix 文件系统，镜像里还得有个能跑的 shell：仓库里没有
现成的 hdc 镜像，所以这里自己编 sh、自己按 a.out（ZMAGIC）打包、自己拼文件系统。

用法：python mkroot.py out/root.img
"""

import os
import struct
import subprocess
import sys

BLOCK = 1024
INODES = 32
DISK_SECTORS = 16384                # 8 MB 硬盘
PART_START = 64                     # 分区从 64 号扇区起，前面留 MBR
ZONES = (DISK_SECTORS - PART_START) * 512 // BLOCK
INODE_BLOCKS = (INODES * 32 + BLOCK - 1) // BLOCK
IMAP_BLOCKS = (INODES + 8191) // 8192
ZMAP_BLOCKS = (ZONES + 8191) // 8192
FIRST_ZONE = 2 + IMAP_BLOCKS + ZMAP_BLOCKS + INODE_BLOCKS

S_IFDIR = 0o040000
S_IFREG = 0o100000
S_IFCHR = 0o020000

TOOLS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".work",
                                      "tools", "w64devkit", "bin"))


def tool(name):
    path = os.path.join(TOOLS, name + ".exe")
    return path if os.path.exists(path) else name


def elf_sections(path):
    """读 ELF 节表，返回 {名字: (偏移, 大小)}。"""
    data = open(path, "rb").read()
    (shoff,) = struct.unpack_from("<I", data, 0x20)
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    (names_off,) = struct.unpack_from("<I", data, shoff + shstrndx * shentsize + 0x10)
    out = {}
    for i in range(shnum):
        base = shoff + i * shentsize
        (name_off,) = struct.unpack_from("<I", data, base)
        end = data.index(b"\0", names_off + name_off)
        name = data[names_off + name_off:end].decode("latin-1")
        addr, off, size = struct.unpack_from("<III", data, base + 0x0C)
        flags, = struct.unpack_from("<I", data, base + 0x08)
        stype, = struct.unpack_from("<I", data, base + 0x04)
        out[name] = (off, size, addr, flags, stype)
    return data, out


def build_program(name, source, out_dir):
    """把 C 编成 ZMAGIC a.out。"""
    obj = os.path.join(out_dir, name + ".o")
    crt = os.path.join(out_dir, "crt.o")
    exe = os.path.join(out_dir, name + ".exe")
    elf = os.path.join(out_dir, name + ".elf")

    def run(line):
        done = subprocess.run(line, capture_output=True, text=True, errors="replace")
        if done.returncode:
            raise SystemExit("%s 失败\n%s" % (line[0], done.stderr[-1500:]))

    if not os.path.exists(crt):
        run([tool("as"), "--32", "-o", crt, os.path.join(os.path.dirname(os.path.abspath(__file__)), "crt.s")])
    run([tool("gcc"), "-m32", "-ffreestanding", "-fno-builtin", "-fno-pic", "-fno-stack-protector",
         "-fno-leading-underscore", "-mno-sse", "-mno-sse2", "-mno-mmx", "-nostdlib",
         "-O0", "-c", source, "-o", obj])
    run([tool("ld"), "-m", "i386pe", "--disable-reloc-section", "-Ttext", "0x0",
         "-e", "start", crt, obj, "-o", exe])
    run([tool("objcopy"), "-O", "elf32-i386", exe, elf])

    data, sections = elf_sections(elf)
    # a.out 是固定装载镜像：按虚拟地址把 .text/.rodata/.data 连续摆好，
    # 否则 .rdata 里的字符串字面量会被漏掉（PE 目标把字面量放 .rdata）。
    progbits = [x for x in sections.values() if x[1] and x[3] & 0x2 and x[4] == 1]
    image_end = max(addr + size for _off, size, addr, _fl, _tp in progbits)
    image = bytearray(image_end)
    for off, size, addr, _fl, _tp in progbits:
        image[addr:addr + size] = data[off:off + size]
    text_size = sections[".text"][1]
    data_size = image_end - text_size
    bss_size = sections.get(".bss", (0, 0, 0, 0, 0))[1]

    header = struct.pack("<8I", 0o413, text_size, data_size, bss_size, 0, 0, 0, 0)
    return header + bytes(BLOCK - len(header)) + bytes(image)


class Fs:
    def __init__(self):
        self.image = bytearray(BLOCK * ZONES)
        self.next_inode = 1
        self.next_zone = FIRST_ZONE
        self.imap = bytearray(IMAP_BLOCKS * BLOCK)
        self.zmap = bytearray(ZMAP_BLOCKS * BLOCK)
        self.inodes = {}

    def bit(self, data, n):
        data[n // 8] |= 1 << (n % 8)

    def zone(self, payload):
        if len(payload) > BLOCK:
            raise SystemExit("单块超过 1 KB")
        zone = self.next_zone
        self.next_zone += 1
        self.image[zone * BLOCK:zone * BLOCK + len(payload)] = payload
        self.bit(self.zmap, zone - FIRST_ZONE + 1)     # 位图第 b 位对应 zone b+FIRST_ZONE-1
        return zone

    def inode(self, mode, size=0, zones=(), nlinks=1):
        nr = self.next_inode
        self.next_inode += 1
        self.bit(self.imap, nr)
        self.inodes[nr] = (mode, size, list(zones), nlinks)
        return nr

    def directory(self, nr, entries, nlinks):
        zones = []
        for start in range(0, max(len(entries), 1), BLOCK // 16):
            chunk = entries[start:start + BLOCK // 16]
            payload = b"".join(struct.pack("<H14s", num, name.encode()) for name, num in chunk)
            zones.append(self.zone(payload))
        self.inodes[nr] = (S_IFDIR | 0o755, len(entries) * 16, zones, nlinks)

    def file(self, mode, payload):
        chunks = [payload[i:i + BLOCK] for i in range(0, len(payload), BLOCK)]
        # minix v1 的 inode 只有 9 个 zone 项：0..7 直接块，第 8 项是一级间接块。
        direct = [self.zone(c) for c in chunks[:8]]
        rest = chunks[8:]
        if not rest:
            return self.inode(mode, len(payload), direct, 1)
        if len(rest) > 512:
            raise SystemExit("文件太大：%d 块超过一级间接上限" % len(chunks))
        indirect = [self.zone(c) for c in rest]
        table = struct.pack("<%dH" % len(indirect), *indirect)
        ptr = self.zone(table)
        return self.inode(mode, len(payload), direct + [ptr], 1)

    def finish(self):
        self.bit(self.imap, 0)               # i 节点 0 不存在，位留空
        self.bit(self.zmap, 0)               # 逻辑块 0 也留空

        super_block = struct.pack("<HHHHHHIHHI", INODES, ZONES, IMAP_BLOCKS, ZMAP_BLOCKS,
                                  FIRST_ZONE, 0, (ZONES - FIRST_ZONE) * BLOCK,
                                  0x137F, 1, ZONES)
        self.image[BLOCK:BLOCK + len(super_block)] = super_block
        self.image[2 * BLOCK:2 * BLOCK + len(self.imap)] = self.imap
        base = (2 + IMAP_BLOCKS) * BLOCK
        self.image[base:base + len(self.zmap)] = self.zmap

        inode_base = (2 + IMAP_BLOCKS + ZMAP_BLOCKS) * BLOCK
        for nr, (mode, size, zones, nlinks) in self.inodes.items():
            raw = struct.pack("<HHIIBB9H", mode, 0, size, 0, 0, nlinks,
                              *(zones + [0] * (9 - len(zones))))
            off = inode_base + (nr - 1) * 32
            self.image[off:off + 32] = raw
        return bytes(self.image)


def main(out_path):
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)

    sh = build_program("sh", os.path.join(here, "sh.c"), out_dir)
    rc = open(os.path.join(here, "rc"), "rb").read()
    hello = open(os.path.join(here, "hello.txt"), "rb").read()

    fs = Fs()
    root = fs.inode(S_IFDIR | 0o755)                  # 1，先占号，最后填目录项
    etc = fs.inode(S_IFDIR | 0o755)                   # 2
    rc_file = fs.file(S_IFREG | 0o644, rc)            # 3
    bin_dir = fs.inode(S_IFDIR | 0o755)               # 4
    sh_file = fs.file(S_IFREG | 0o755, sh)            # 5
    dev = fs.inode(S_IFDIR | 0o755)                   # 6
    tty0 = fs.inode(S_IFCHR | 0o666, 0, [0o2000])      # 7
    tty1 = fs.inode(S_IFCHR | 0o666, 0, [0o2001])      # 8
    tty2 = fs.inode(S_IFCHR | 0o666, 0, [0o2002])      # 9
    hello_file = fs.file(S_IFREG | 0o644, hello)      # 10

    tty0 and tty1 and tty2 and root                # 只是留个记号，号在下面用到

    fs.directory(1, [(".", 1), ("..", 1), ("etc", etc), ("bin", bin_dir),
                  ("dev", dev), ("hello.txt", hello_file)], 5)
    fs.directory(etc, [(".", etc), ("..", 1), ("rc", rc_file)], 2)
    fs.directory(bin_dir, [(".", bin_dir), ("..", 1), ("sh", sh_file)], 2)
    fs.directory(dev, [(".", dev), ("..", 1), ("tty0", tty0), ("tty1", tty1), ("tty2", tty2)], 2)

    fs_image = fs.finish()
    disk = bytearray(DISK_SECTORS * 512)
    disk[0x1BE + 0] = 0x80                              # 活动分区
    disk[0x1BE + 4] = 0x81                              # minix 分区类型
    struct.pack_into("<II", disk, 0x1BE + 8, PART_START, DISK_SECTORS - PART_START)
    disk[510] = 0x55
    disk[511] = 0xAA
    disk[PART_START * 512:PART_START * 512 + len(fs_image)] = fs_image
    open(out_path, "wb").write(bytes(disk))
    print("root.img %d 字节（分区表 + %d 块 minix），%d i 节点, sh %d 字节"
          % (len(disk), ZONES, fs.next_inode - 1, len(sh)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out/root.img")
