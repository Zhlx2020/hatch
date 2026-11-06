#include "keyboard.h"
/* 扫描码 → ASCII，只覆盖常用键，够验证调试链路 */
static const char map[128] = {
    0, 27, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', '\b',
    '\t', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\n',
    0, 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '`',
    0, '\\', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 0, '*', 0, ' ',
};

int keyboard_poll(void)
{
    unsigned char status;
    __asm__ volatile("inb $0x64, %0" : "=a"(status));
    if ((status & 1) == 0)
        return 0;

    unsigned char code;
    __asm__ volatile("inb $0x60, %0" : "=a"(code));
    if (code & 0x80)
        return 0;                       /* 松键 */
    if (code >= sizeof(map))
        return 0;
    return map[code];
}
