/* 内核链接脚本：钉在 0x10000，入口 _start，不要 PE 头 */
ENTRY(_start)
SECTIONS
{
  . = 0x10000;
  .text   : { *(.text*) }
  .rodata : { *(.rodata*) }
  .data   : { *(.data*) }
  .bss    : { *(.bss*) *(COMMON) }
}
