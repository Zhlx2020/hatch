; 0 号扇区只干一件小事：把第二级（setup，4 个扇区）读到 0x9000 并跳过去。
; 引导扇区只有 512 字节，装不下的东西全放 setup.asm。
bits 16
org 0x7c00

SETUP_SEG equ 0x900
SETUP_SECTORS equ 4

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7c00
    mov [drive], dl

    mov ax, SETUP_SEG
    mov es, ax
    xor bx, bx
    mov cx, 2                  ; 第 2 扇区开始
    mov word [left], SETUP_SECTORS
.read:
    mov ax, 0x0201
    mov dl, [drive]
    int 0x13
    jc  .error
    dec word [left]
    jz  .ready
    add bx, 512
    inc cl
    jmp .read
.ready:
    jmp SETUP_SEG * 16

.error:
    mov si, message
.print:
    lodsb
    test al, al
    jz .hang
    mov ah, 0x0e
    int 0x10
    jmp .print
.hang:
    hlt
    jmp .hang

drive: db 0
left:  dw 0
message: db "read error", 13, 10, 0

times 510-($-$$) db 0
dw 0xaa55
