/* 高亮自查用的样例：预处理、函数调用与定义、类型、字符串、注释 */
#include <stdint.h>
#include "screen.h"
   #define BOARD_W 80
#define SHOUT(x) screen_write(x, 0x0f)

struct cell {
    uint8_t ch;
    uint8_t attr;
};

static int scaled(int value, int factor)
{
    return value * factor;
}

void _start(void)
{
    struct cell row[BOARD_W];
    screen_clear();
    screen_write("hello\n", 0x0a);
    for (int i = 0; i < BOARD_W; i++) {
        row[i].ch = (uint8_t)scaled(i, 2);
        screen_write_char(row[i].ch, row[i].attr);
    }
    /* 块注释：字符串里的 "引号" 不算字符串 */
    while (1) {
        int key = keyboard_poll();
        if (key == 27) return;
    }
}
