; 显示测试用：切到 320x200 图形模式，整屏涂色块，检查缩放和切换分辨率
bits 16
org 0x7c00

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7c00

    mov ax, 0x0013
    int 0x10

    mov ax, 0xa000
    mov es, ax
    xor di, di
    mov cx, 320 * 200
    mov al, 1
.fill:
    stosb
    loop .fill

    mov ax, 0xa000
    mov es, ax
    mov cx, 320
    mov di, 0
    mov bx, 320 * 199
.top:
    mov al, 15
    mov es:[di], al
    mov es:[bx + di], al
    inc di
    loop .top

    mov cx, 200
    xor di, di
    mov bx, 319
.left:
    mov al, 15
    mov es:[di], al
    mov es:[bx + di], al
    add di, 320
    loop .left

    mov di, 320 * 60
    mov cx, 80
    mov bx, 60
.box:
    push di
    push cx
    mov cx, 80
    mov al, 14
.inner:
    mov es:[di], al
    inc di
    loop .inner
    pop cx
    pop di
    add di, 320
    dec bx
    jnz .box
.hang:
    hlt
    jmp .hang

times 510-($-$$) db 0
dw 0xaa55
