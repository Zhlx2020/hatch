BITS 16
ORG 0x7C00

; 扫描码观察器：把 0x60 读到的每个字节以两位十六进制打到串口。
start:
    cli
    xor ax, ax
    mov ds, ax
    mov ss, ax
    mov sp, 0x7C00
    sti
    call serial_init
.loop:
    in al, 0x64
    test al, 1
    jz .loop
    in al, 0x60
    push ax
    shr al, 4
    call hex
    pop ax
    and al, 0x0F
    call hex
    mov al, ' '
    call out
    jmp .loop

hex:
    cmp al, 10
    jb .digit
    add al, 'a' - 10
    jmp out
.digit:
    add al, '0'
    jmp out

out:
    push ax
    push dx
.wait:
    mov dx, 0x3FD
    in al, dx
    test al, 0x20
    jz .wait
    pop dx
    pop ax
    push ax
    push dx
    mov dx, 0x3F8
    out dx, al
    pop dx
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

times 510-($-$$) db 0
dw 0xAA55
