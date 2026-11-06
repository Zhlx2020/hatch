; 屏幕测试用：画一圈边框 + 列标尺，用来量有没有截断、起点对不对
bits 16
org 0x7c00

VGA  equ 0xb800
ATTR equ 0x0f

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7c00

    mov ax, VGA
    mov es, ax
    xor di, di
    mov cx, 80 * 25
.fill:
    mov ax, 0x0720
    stosw
    loop .fill

    mov ax, VGA
    mov es, ax
    mov cx, 80
    mov di, 0
    mov bx, 80 * 2 * 24
.top:
    mov ax, 0x0f23
    mov es:[di], ax
    mov es:[di + bx], ax
    add di, 2
    loop .top

    mov cx, 25
    xor di, di
.left:
    mov ax, 0x0f7c
    mov es:[di], ax
    mov es:[di + 158], ax
    add di, 160
    loop .left

    mov di, 160 * 2
    mov si, ruler
    mov cx, 8
.copy:
    push cx
    mov cx, 10
.inner:
    mov al, [si]
    mov ah, ATTR
    mov es:[di], ax
    add di, 2
    inc si
    loop .inner
    pop cx
    mov si, ruler
    loop .copy

    mov di, 160 * 2 * 12
    mov si, mid
    call puts

    mov di, 160 * 2 * 24 - 6
    mov si, bottom
    call puts
.hang:
    hlt
    jmp .hang

puts:
    push ax
.next:
    lodsb
    test al, al
    jz .done
    mov ah, ATTR
    mov es:[di], ax
    add di, 2
    jmp .next
.done:
    pop ax
    ret

ruler:  db "0123456789"
mid:    db "MID-ROW-OK", 0
bottom: db "END", 0

times 510-($-$$) db 0
dw 0xaa55
