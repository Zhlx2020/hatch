import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/disasm.py"
s = p.read_text(encoding="utf-8")
s = s.replace('''def load(image, syntax=DEFAULT):''',
'''def build_split(image, regions, out=None):
    """Disassemble several (file, address) regions into one sorted map.

    A boot stub and a kernel linked far apart cannot share one linear pass: the
    stub is at 0x7C00 and the kernel at 0x10000, so each region gets its own
    base and the results are merged by address.
    """
    written = []
    for syntax in SYNTAXES:
        lines = []
        for source, base in regions:
            result = subprocess.run(
                [config.OBJDUMP, "-D", "-b", "binary", "-m", "i386",
                 "-M", "i8086,%s" % syntax, "--adjust-vma=0x%x" % base, source],
                capture_output=True, text=True,
            )
            for line in result.stdout.splitlines():
                match = LINE.match(line)
                if match:
                    lines.append((int(match.group(1), 16), match.group(2).strip(),
                                  match.group(3)))
        lines.sort(key=lambda row: row[0])
        target = out or path(image, syntax)
        with open(target, "w", newline="\\n", encoding="utf-8") as fh:
            fh.write("\\n".join("%08x: %-24s %s" % row for row in lines))
        written.append(target)
    return written[0]


def load(image, syntax=DEFAULT):''')
p.write_text(s, encoding="utf-8", newline="\n")

c = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/config.py"
t = c.read_text(encoding="utf-8")
print(t)
