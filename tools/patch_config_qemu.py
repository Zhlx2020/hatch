import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/config.py"
s = p.read_text(encoding="utf-8")

s = s.replace('NASM = r"C:\\Users\\zlx\\Documents\\deepseek-harness\\default-workspace\\osdev-lab\\tools\\nasm-3.02\\nasm.exe"',
              'NASM = r"C:\\Users\\zlx\\Documents\\deepseek-harness\\default-workspace\\osdev-lab\\tools\\nasm-3.02\\nasm.exe"\n'
              'OBJDUMP = r"C:\\Users\\zlx\\Documents\\deepseek-harness\\default-workspace\\oslab\\.work\\w64\\w64devkit\\bin\\objdump.exe"\n'
              'QEMU = r"C:\\Program Files\\qemu\\qemu-system-i386.exe"')

s = s.replace("RFB_PORT = 5900", "RFB_PORT = 5901\nGDB_PORT = 5913\nSERIAL_PORT = 5914\nVNC_HOST_PORT = 1\nBACKEND = \"qemu\"")
p.write_text(s, encoding="utf-8", newline="\n")
print(s)
