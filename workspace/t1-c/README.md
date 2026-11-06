# C hello

最小的 32 位 C 内核：16 位引导扇区负责载入内核、开 A20、进保护模式，然后跳进
`src/kmain.c`。内核只做 VGA 文本输出和键盘轮询，够用来演示断点和单步。

- 入口只有 `_start`，不链接 libc，全部 `-ffreestanding -O0`
- 在编辑器里点行号打红点 → 启动 → 会在该行停下
- `boot/boot.asm` 与 `boot/kernel.ld` 一般不用改

改内存布局：见 `oslab.toml` 里的 `kind/entry/sources`。
