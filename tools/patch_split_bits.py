import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/disasm.py"
s = p.read_text(encoding="utf-8")
s = s.replace('''def build_split(image, regions, out=None):
    """Disassemble several (file, address) regions into one sorted map.

    A boot stub and a kernel linked far apart cannot share one linear pass: the
    stub is at 0x7C00 and the kernel at 0x10000, so each region gets its own
    base and the results are merged by address.
    """''',
'''def build_split(image, regions, out=None):
    """Disassemble several (file, address, bits) regions into one sorted map.

    A boot stub and a kernel linked far apart cannot share one linear pass: the
    stub is 16-bit at 0x7C00 and the kernel is 32-bit at 0x10000, so each region
    gets its own base and decoder and the results are merged by address.
    """''')
s = s.replace('''        for source, base in regions:
            result = subprocess.run(
                [config.OBJDUMP, "-D", "-b", "binary", "-m", "i386",
                 "-M", "i8086,%s" % syntax, "--adjust-vma=0x%x" % base, source],
                capture_output=True, text=True,
            )''',
'''        for source, base, bits in regions:
            arch = "i8086" if bits == 16 else "i386"
            result = subprocess.run(
                [config.OBJDUMP, "-D", "-b", "binary", "-m", "i386",
                 "-M", "%s,%s" % (arch, syntax), "--adjust-vma=0x%x" % base, source],
                capture_output=True, text=True,
            )''')
p.write_text(s, encoding="utf-8", newline="\n")

c = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/cbuild.py"
t = c.read_text(encoding="utf-8")
t = t.replace("disasm.build_split(image, [(stub, plan[\"base\"]), (flat, KERNEL_BASE)])",
              "disasm.build_split(image, [(stub, plan[\"base\"], 16), (flat, KERNEL_BASE, 32)])")
c.write_text(t, encoding="utf-8", newline="\n")
print("ok")
