"""Show what a built image actually looks like on disk.

The reader never guesses: every region comes from the build (the boot stub, the
kernel payload) or from the padding the image writer added, and every claim is
checked against the bytes before it is reported. Suspect layouts are flagged
instead of being drawn as if they were fine.
"""
import json
import os

SECTOR = 512
FLOPPY = 1474560
PARTS = "layout.json"

KINDS = {
    "boot": "引导扇区",
    "mbr": "主引导记录",
    "code": "代码与数据",
    "stage": "引导链后级",
    "data": "数据",
    "pad": "填充（0x00，占位到磁盘末尾）",
    "unknown": "未归类",
}
NOTE = {
    "boot": "整块 512 字节，最后由 0xAA55 收尾，由固件载入 0x7C00。",
    "mbr": "前 446 字节是引导代码，接着 4 条 16 字节分区表项。",
    "code": "构建产物本体。",
    "pad": "QEMU 只按扇区读盘，尾巴补零凑成一张软盘。",
}


def record(image, parts):
    """Build 之后记下各段的位置，可视化时按段标注。"""
    rows = []
    for part in parts:
        offset, size, kind, label, base = part
        if size <= 0:
            continue
        rows.append({"offset": offset, "size": size, "kind": kind,
                     "label": label, "base": base})
    try:
        with open(image + "." + PARTS, "w", encoding="utf-8") as fh:
            json.dump({"parts": rows}, fh)
    except OSError:
        pass


def _parts(image, size):
    try:
        with open(image + "." + PARTS, encoding="utf-8") as fh:
            rows = json.load(fh).get("parts") or []
    except (OSError, ValueError):
        rows = []
    out, cursor = [], 0
    if not rows and size:
        # 没有构建记录时，头一个扇区按引导扇区看，剩下的只能是填充
        head = min(size, SECTOR)
        out.append({"offset": 0, "size": head, "kind": "boot",
                    "label": "引导扇区（构建没留记录）", "base": 0x7C00})
        cursor = head
    for row in sorted(rows, key=lambda item: item["offset"]):
        start = max(0, min(int(row["offset"]), size))
        if start > cursor:
            out.append({"offset": cursor, "size": start - cursor, "kind": "unknown",
                        "label": "构建没说明用途的一段", "base": 0})
        end = max(start, min(start + int(row["size"]), size))
        if end > start:
            out.append({"offset": start, "size": end - start, "kind": row.get("kind"),
                        "label": row.get("label") or "", "base": int(row.get("base") or 0)})
        cursor = max(cursor, end)
    if cursor < size:
        out.append({"offset": cursor, "size": size - cursor, "kind": "pad",
                    "label": "尾部填充", "base": 0})
    return out


def _texty(raw):
    """字节够不够像文字：够才当成 OEM 标记写出来。"""
    return sum(1 for one in raw if 32 <= one < 127) >= len(raw) * 0.6


def _printable(raw):
    """控制字节原样看不见，转成 \\xNN。"""
    return "".join(chr(one) if 32 <= one < 127 else "\\x%02x" % one for one in raw).strip()


def _fields(data, region, warnings):
    """引导扇区里值得看一眼的字节，逐项指出来。"""
    if region["offset"] or region["size"] < SECTOR:
        return []
    head = data[:SECTOR]
    rows = []
    jump = head[0:3]
    rows.append({"k": "开头 3 字节", "v": jump.hex(" "),
                 "note": "标准是 EB xx 90 或 E9 xx xx：先跳，再留 OEM 标记的位置"})
    oem = head[3:11]
    if oem.strip(b"\x00 ") and _texty(oem):
        rows.append({"k": "3-10 字节", "v": _printable(oem),
                     "note": "OEM 标记，FAT 卷里是格式化工具名"})
    bpb = head[11:62]
    bpb_like = (bpb[0:2] in (b"\x00\x02", b"\x01\x00")
                or bpb[11:13] == b"\x02\x00")
    if bpb_like:
        rows.append({"k": "11-61 字节", "v": "有 BPB 字段",
                     "note": "按 FAT 卷头解释：扇区大小 %d、每簇扇区 %d、FAT 数 %d、根目录项 %d"
                             % (int.from_bytes(bpb[0:2], "little"),
                                bpb[2], bpb[5],
                                int.from_bytes(bpb[6:8], "little"))})
    if not jump.startswith(b"\xeb") and not jump.startswith(b"\xe9"):
        note = "固件会从第 0 字节顺着执行"
        if bpb_like:
            warnings.append("开头不是跳转指令（%s），但 11 字节处像 BPB 卷头，"
                            "按 FAT 卷用时固件会先读卷头再跳，可能跑偏" % jump.hex(" "))
        else:
            rows[-1]["note"] += "；这里没按跳转开头，%s" % note
    table = head[0x1BE:0x1FE]
    entries = [table[i:i + 16] for i in range(0, 64, 16)]
    live = [e for e in entries if e[4] and e[4] != 0]
    if live:
        region["kind"] = "mbr"
        for index, entry in enumerate(entries):
            if not entry[4]:
                continue
            lba = int.from_bytes(entry[8:12], "little")
            count = int.from_bytes(entry[12:16], "little")
            rows.append({"k": "分区 %d" % (index + 1),
                         "v": "类型 0x%02X，%d 扇区，从第 %d 扇区起%s"
                              % (entry[4], count, lba,
                                 "（可引导标记 0x80）" if entry[0] == 0x80 else ""),
                         "note": "起始字节 %d" % (0x1BE + index * 16)})
            if lba * SECTOR + count * SECTOR > region["size"] + len(data):
                warnings.append("分区 %d 越过了镜像末尾" % (index + 1))
    tail = head[510:512]
    rows.append({"k": "510-511 字节", "v": tail.hex(" "),
                 "note": "必须是 55 AA，固件才认这是可引导扇区"})
    if tail != b"\x55\xaa":
        warnings.append("结尾签名不是 55 AA")
    return rows


def describe(image, marks=()):
    """一份能直接画出来的镜像布局。"""
    if not os.path.isfile(image):
        raise FileNotFoundError(image)
    size = os.path.getsize(image)
    with open(image, "rb") as fh:
        data = fh.read()
    warnings = []
    regions = _parts(image, size)
    for region in regions:
        region["kind_name"] = KINDS.get(region["kind"], region["kind"])
        region["note"] = NOTE.get(region["kind"], "")
        start = region["offset"]
        region["hex"] = data[start:start + 16].hex(" ")
        if region["kind"] in ("boot", "mbr"):
            region["fields"] = _fields(data, region, warnings)
        if region["kind"] == "code" and region["base"]:
            region["addr"] = "0x%08x" % (region["base"] + region["offset"]
                                         if region["offset"] == 0 else region["base"])
    placed = []
    for mark in marks:
        addr = int(mark.get("addr") or 0)
        for region in regions:
            base = region["base"]
            if not base or region["kind"] not in ("code", "boot", "data"):
                continue
            offset = region["offset"] + (addr - base)
            if region["offset"] <= offset < region["offset"] + region["size"]:
                placed.append({"line": mark.get("line"), "file": mark.get("file"),
                               "addr": "0x%08x" % addr, "offset": offset})
                break
    if size % SECTOR:
        warnings.append("镜像 %d 字节不是整扇区" % size)
    if size > FLOPPY and not any(r["kind"] == "mbr" for r in regions):
        warnings.append("超过软盘容量")
    zero = data.count(0)
    return {
        "size": size,
        "sectors": size // SECTOR if SECTOR else 0,
        "regions": regions,
        "marks": placed,
        "warnings": warnings,
        "zero": zero,
        "used": size - zero,
    }
