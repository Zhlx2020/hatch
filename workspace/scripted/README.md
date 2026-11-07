# 自己的构建命令

清单里写了 `build`，内置流水线整条让开：`make`、`bash build.sh`、一串 gcc 都行，
路径和参数你自己的。IDE 只看命令跑没跑通、产物在不在，不掺和过程。

`boot.asm` 是个只会打一行字的引导扇区，`make.py` 用 nasm 汇编后补零到一张软盘。
PATH 上已经放好本机的 nasm / gcc / ld / objcopy，直接叫名字就行。

想看行号映射和 ELF 结构，就再产出 `elf` / `map` 并在清单里声明。
