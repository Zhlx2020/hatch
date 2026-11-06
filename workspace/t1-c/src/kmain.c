/* 屏幕与键盘：直接操作 VGA 文本区（0xB8000）和 0x60/0x64 端口 */
#include "screen.h"
#include "keyboard.h"

void _start(void)
{
    screen_clear();
    screen_write("C kernel up, Esc to quit\n\n", 0x0A);
    screen_write("Breakpoints: click a line number in the editor.\n", 0x07);
    

    for (;;)
    {
        int key = keyboard_poll();
        if (key == 0)
            continue;
        if (key == 27)
        {
            screen_write("\nbye\n", 0x07);
            for (;;)
                __asm__ volatile("hlt");
        }
        char text[2] = {(char)key, 0};
        screen_write(text, 0x0F);
    }
}
