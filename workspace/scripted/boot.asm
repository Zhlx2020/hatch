bits 16
org 0x7c00

mov si, msg
.print:
    lodsb
    test al, al
    jz  .hang
    mov ah, 0x0e
    int 0x10
    jmp .print
.hang:
    hlt
    jmp .hang

msg: db "scripted build ok", 13, 10, 0

times 510-($-$$) db 0
dw 0xaa55
