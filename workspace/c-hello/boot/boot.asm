; 引导扇区：把内核读进来，开 A20，进保护模式，跳到 0x10000
bits 16
org 0x7c00

KERNEL_SEG equ 0x1000          ; 0x1000:0000 = 0x10000
SECTORS    equ 32

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7c00
    mov [drive], dl

    mov ax, KERNEL_SEG
    mov es, ax
    xor bx, bx
    mov ah, 0x02               ; int 13h 读盘
    mov al, SECTORS
    mov ch, 0
    mov cl, 2                  ; 从第 2 扇区开始
    mov dh, 0
    mov dl, [drive]
    int 0x13
    jc  disk_error

    call a20_on
    lgdt [gdtr]
    mov eax, cr0
    or  eax, 1
    mov cr0, eax
    jmp 0x08:pm_start

disk_error:
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

a20_on:
    in  al, 0x92
    or  al, 2
    out 0x92, al
    ret

bits 32
pm_start:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov esp, 0x90000
    jmp KERNEL_SEG * 16

gdt:
    dq 0
    dw 0xffff, 0x0000, 0x9a00, 0x00cf    ; 代码段 0-4G
    dw 0xffff, 0x0000, 0x9200, 0x00cf    ; 数据段 0-4G
gdtr:
    dw gdtr - gdt - 1
    dd gdt

drive:   db 0
message: db "disk error", 13, 10, 0

times 510-($-$$) db 0
dw 0xaa55
