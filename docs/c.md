# C 工程

## 为什么不做裸 C

C 要 32 位平坦寻址，引导扇区是 16 位实模式。所以每个 C 工程都由三件东西组成：

- `boot/boot.asm`：512 字节引导扇区，`int 13h` 把内核读进 0x10000，开 A20、装 GDT、进保护模式、
  远跳过去。结尾必须是 `0xAA55`
- `boot/kernel.ld`：把入口钉在 0x10000 的链接脚本
- `src/*.c`：内核本体，只有 `_start`，不链 libc

`oslab.toml` 把这三件事的关系写清楚，`services/project.py` 负责校验。

## 怎么编

`services/cbuild.py`：

1. `gcc -m32 -ffreestanding -fno-pic -fno-stack-protector -fno-asynchronous-unwind-tables -O0 -g -c`
2. `ld -m i386pe --disable-reloc-section -T kernel.ld -e _start`
3. `objcopy -O binary --strip-debug -j .text -j .rdata -j .rodata -j .data`
4. 引导扇区 + 内核 + 零填充 = 1.44 MB 镜像

这套 binutils 只有 PE 目标，所以用 `objcopy` 取段而不是 `--oformat binary`：PE 的
`.reloc` 和调试节会让后者报「file truncated」。PE 还会把 `.rodata` 收进 `.rdata`，
两个名字都要取，否则字符串会凭空消失。`-disable-reloc-section` 顺带消掉了基址重定位警告。

`-O0` 是刻意的：优化会把源码行合并、把变量搬进寄存器，行断点随之漂移。要性能自己加 `-O2`，
代价是断点可能跳行。

## 断点怎么落地

`objdump -dl kernel.exe` 输出里 `文件:行号` 后面跟着该行的第一条指令地址，
`services/linemap.py` 把这张表翻成 `路径 → {行: 地址}`。汇编则反过来读 nasm 的 `.lst`。

点行号 → `GET /api/line` 查地址 → 红点；点运行 → 服务端构建完**先按行号写断点再放行**。
执行流停在断点上时 `eip` 反查回行号，编辑器高亮同一行。

## 限制

- 内核最大 15.5 KB（引导扇区只读 32 扇区），超了会直接报错
- 没有分页、没有中断处理、没有 libc；要这些得自己写，模板只到 VGA 文本和键盘轮询

## 工具链

`config.C_GCC / C_LD / C_OBJCOPY` 指向 `.work/w64/w64devkit/bin`。编译器需要一个可写的临时目录，
`cbuild` 会把 `TMP/TEMP/TMPDIR` 指到本次会话目录（系统 `%TEMP%` 在某些机器上写不进去）。
