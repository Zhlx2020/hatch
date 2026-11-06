#pragma once

/* 返回 0 表示没按键；否则返回 ASCII（Esc = 27） */
int keyboard_poll(void);
