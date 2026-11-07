ENTRY(startup_32)
SECTIONS
{
  . = __KERNEL_BASE__;
  .text : { *(.text) }
  .data : { *(.data) }
  .bss : { *(.bss) *(COMMON) }

  /* 0.11 的代码按 0x1000 对齐在内核尾后放页表，顺手用 ld 默认脚本里的 end 当边界；
     换了自己的脚本就得自己给它，否则 buffer.c 里那句 &end 链不上。 */
  . = ALIGN(0x1000);
  end = .;
  _end = .;
}
