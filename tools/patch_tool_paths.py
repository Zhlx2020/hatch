import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/config.py"
s = p.read_text(encoding="utf-8")
s = s.replace('QEMU = r"C:\\Program Files\\qemu\\qemu-system-i386.exe"',
              'QEMU = r"C:\\Program Files\\qemu\\qemu-system-i386.exe"\n'
              '_W64 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".work", "w64", "w64devkit", "bin")\n'
              'C_GCC = os.path.abspath(os.path.join(_W64, "gcc.exe"))\n'
              'C_LD = os.path.abspath(os.path.join(_W64, "ld.exe"))\n'
              'C_OBJCOPY = os.path.abspath(os.path.join(_W64, "objcopy.exe"))')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
