bits 16
org 0x7c00
    jmp start

%include "banner.inc"
start:
    cli
    say hello
    hlt
hello: db "INCLUDE OK", 13, 10, 0
times 510-($-$$) db 0
dw 0xaa55
