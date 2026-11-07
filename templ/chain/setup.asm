; 第二级：被读到 0x9000 后跳进来。这里已经不在 512 字节的框里了，
; 可以直接往显存写、开 A20、装 GDT、进保护模式——真项目就在这里搬内核。
bits 16
org 0x9000

    mov ax, 0xb800
    mov es, ax
    xor di, di
    mov si, banner
.write:
    lodsb
    test al, al
    jz  .done
    mov ah, 0x0e
    mov [es:di], ax
    add di, 2
    jmp .write
.done:
    hlt
    jmp .done

banner: db "stage 2 running from 0x9000", 0

; 这一级会被整扇区取整，多出来的补零就行
times (4 * 512) - ($ - $$) db 0
