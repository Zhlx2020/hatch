# C 工程

## 为什么不做裸 C

C 要 32 位平坦寻址，引导扇区是 16 位实模式。所以每个 C 工程都由三件东西组成：

- `boot/boot.asm`：512 字节引导扇区，逐扇区把内核读到 `kernel` 指定的地址，开 A20、装 GDT、
  进保护模式、远跳过去。结尾必须是 `0xAA55`
- `boot/kernel.ld`：把内核钉在 `kernel`（默认 0x10000）的链接脚本；也可以只写
  `__KERNEL_BASE__` 让构建来代入

引导链可以多级：`stages` 里第二个及以后的文件按整扇区摆在后面，512 字节装不下的东西放去那里。
仓库自带的 stub 已经按扇区循环读盘，不赌 BIOS 的批量读。
- `src/*.c`：内核本体，只有 `_start`，不链 libc

`oslab.toml` 把这三件事的关系写清楚，`services/project.py` 负责校验。

## 怎么编

`services/cbuild.py`：

1. `gcc -m32 -ffreestanding -fno-pic -fno-stack-protector -fno-asynchronous-unwind-tables -O0 -g -c`
   （清单里的 `cflags` 追加在后面，`includes` 追加 `-I`）
2. `ld -m i386pe --disable-reloc-section -T <link> -e <symbol>`（`symbol` 默认 `_start`）
3. `objcopy -O binary --strip-all`——不挑节，自定义节不会被丢掉
4. 引导链按顺序摆、内核摆在最后一个整扇区之后、零填充到 1.44 MB

汇编源（`.asm` / `.s`）先走 `nasm -f elf32`，再和 `.c` 一起参与链接。

这套 binutils 只有 PE 目标，所以用 `objcopy` 转二进制而不是 `--oformat binary`：PE 的
`.reloc` 和调试节会让后者报「file truncated」。`-disable-reloc-section` 顺带消掉了基址重定位警告。

`-O0` 是刻意的：优化会把源码行合并、把变量搬进寄存器，行断点随之漂移。要性能自己加 `-O2`，
代价是断点可能跳行。

## 断点怎么落地

`objdump -dl kernel.exe` 输出里 `文件:行号` 后面跟着该行的第一条指令地址，
`services/linemap.py` 把这张表翻成 `路径 → {行: 地址}`。汇编则反过来读 nasm 的 `.lst`。

点行号 → `GET /api/line` 查地址 → 红点；点运行 → 服务端构建完**先按行号写断点再放行**。
执行流停在断点上时 `eip` 反查回行号，编辑器高亮同一行。

## 限制

- 上限只剩磁盘：1.44 MB（2880 扇区），整张镜像装不下才报错。读得动多少由引导链负责，
  用仓库自带 stub 时它按内核实际扇区数循环读
- 内核地址写在 `kernel` 和链接脚本里，不做重定位；想让内核落在别处就改这两个地方
- 没有分页、没有中断处理、没有 libc；要这些得自己写，模板只到 VGA 文本和键盘轮询

## 工具链

`config.C_GCC / C_LD / C_OBJCOPY` 指向 `.work/w64/w64devkit/bin`。编译器需要一个可写的临时目录，
`cbuild` 会把 `TMP/TEMP/TMPDIR` 指到本次会话目录（系统 `%TEMP%` 在某些机器上写不进去）。
