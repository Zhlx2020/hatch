#include "screen.h"

#define COLS 80
#define ROWS 25
#define VIDEO ((volatile unsigned short *)0xB8000)

static int row;
static int col;

static void scroll(void)
{
    if (row < ROWS)
        return;
    for (int y = 1; y < ROWS; y += 1)
        for (int x = 0; x < COLS; x += 1)
            VIDEO[(y - 1) * COLS + x] = VIDEO[y * COLS + x];
    for (int x = 0; x < COLS; x += 1)
        VIDEO[(ROWS - 1) * COLS + x] = 0x0720;
    row = ROWS - 1;
}

void screen_clear(void)
{
    for (int i = 0; i < COLS * ROWS; i += 1)
        VIDEO[i] = 0x0720;
    row = 0;
    col = 0;
}

void screen_write(const char *text, unsigned char colour)
{
    for (; *text; text += 1)
    {
        if (*text == '\n')
        {
            col = 0;
            row += 1;
            scroll();
            continue;
        }
        VIDEO[row * COLS + col] = (unsigned short)(colour << 8 | (unsigned char)*text);
        col += 1;
        if (col == COLS)
        {
            col = 0;
            row += 1;
            scroll();
        }
    }
}
