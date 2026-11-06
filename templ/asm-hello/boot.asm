bits 16
org 0x7c00

; 最小 hello：直接用 BIOS 输出一行字就停下
start:
    cli
    xor ax, ax
    mov ds, ax
    mov ss, ax
    mov sp, 0x7c00
    mov si, message
    mov ah, 0x0e
.next:
    lodsb
    test al, al
    jz .done
    int 0x10
    jmp .next
.done:
    hlt
    jmp .done

message: db "hello from asm", 13, 10, 0

times 510-($-$$) db 0
dw 0xaa55
