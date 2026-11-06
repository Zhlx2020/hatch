import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/cbuild.py"
s = p.read_text(encoding="utf-8")

# PE 把 .rodata 收进 .rdata：两个名字都要取，否则字符串丢失
s = s.replace('''    _run([tool("objcopy"), "-O", "binary", "-j", ".text", "-j", ".rodata",
          "-j", ".data", kernel, flat], env)''',
'''    _run([tool("objcopy"), "-O", "binary", "--strip-debug",
          "-j", ".text", "-j", ".rdata", "-j", ".rodata", "-j", ".data",
          kernel, flat], env)''')

s = s.replace('''SECTOR = 512
FLOPPY = 1474560''', '''SECTOR = 512
FLOPPY = 1474560
LOAD_SECTORS = 32                     # 与 boot.asm 的 SECTORS 保持一致
KERNEL_LIMIT = (LOAD_SECTORS - 1) * SECTOR''')

s = s.replace('''    data = bytearray(head) + body''',
'''    if len(body) > KERNEL_LIMIT:
        raise AssembleError("内核 %d 字节，引导扇区只能载入 %d" % (len(body), KERNEL_LIMIT))
    data = bytearray(head) + body''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
