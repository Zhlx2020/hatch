BITS 16
ORG 0x7C00

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00

    call serial_init
    call cls
    mov si, msg
.next:
    lodsb
    test al, al
    jz .done
    call putc
    jmp .next
.done:
    jmp $

cls:                        ; 用空格铺满 80x25 文本屏
    push ax
    push cx
    push di
    push es
    mov ax, 0xB800
    mov es, ax
    xor di, di
    mov cx, 2000
    mov ax, 0x0A20
    rep stosw
    mov word [cursor], 0
    pop es
    pop di
    pop cx
    pop ax
    ret

serial_init:
    mov dx, 0x3F9
    xor al, al
    out dx, al
    mov dx, 0x3FB
    mov al, 0x80
    out dx, al
    mov dx, 0x3F8
    mov al, 1
    out dx, al
    mov dx, 0x3F9
    xor al, al
    out dx, al
    mov dx, 0x3FB
    mov al, 0x03
    out dx, al
    mov dx, 0x3FA
    mov al, 0xC7
    out dx, al
    ret

putc:                       ; al = 要输出的字符：同时进串口和 VGA
    push ax
    push bx
    push dx
    push es
    push di
    cmp al, 10
    je .newline
    cmp al, 13
    je .done
    mov ah, al              ; 串口
.wait:
    mov dx, 0x3FD
    in al, dx
    test al, 0x20
    jz .wait
    mov dx, 0x3F8
    mov al, ah
    out dx, al
    mov bx, 0xB800          ; VGA 文本缓冲
    mov es, bx
    mov di, [cursor]
    mov ah, 0x0A
    mov [es:di], ax
    add di, 2
    mov [cursor], di
    jmp .done
.newline:
    mov ax, [cursor]
    mov bx, 160
    xor dx, dx
    div bx
    inc ax
    mul bx
    cmp ax, 4000
    jb .store
    xor ax, ax
.store:
    mov [cursor], ax
.done:
    pop di
    pop es
    pop dx
    pop bx
    pop ax
    ret

cursor: dw 0

msg: db "HELLO FROM 0x7C00", 13, 10, 0

times 510-($-$$) db 0
dw 0xAA55
