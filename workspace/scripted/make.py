# 演示型构建脚本：汇编引导扇区，补零到一张软盘。
# 真实项目这里会是 make 或者一串 gcc/ld，路径由你定，IDE 不看过程只看产物。
import os
import subprocess

os.makedirs("out", exist_ok=True)
subprocess.run(["nasm", "-f", "bin", "boot.asm", "-o", "out/boot.img"], check=True)

data = open("out/boot.img", "rb").read()
with open("out/boot.img", "wb") as fh:
    fh.write(data + b"\x00" * (1474560 - len(data)))
