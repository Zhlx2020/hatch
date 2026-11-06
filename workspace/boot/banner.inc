%macro say 1
    mov si, %1
    call puts
%endmacro
puts:
    lodsb
    test al, al
    jz .end
    mov ah, 0x0e
    mov bx, 7
    int 0x10
    jmp puts
.end:
    ret
