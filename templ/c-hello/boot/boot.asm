; 引导扇区：一个扇区一个扇区地把内核读进来，开 A20，进保护模式，跳过去。
;
; 两个数字由构建代入（清单里改 kernel，别在这里硬写）：
;   KERNEL_SEG 内核所在段（0x10000 → 0x1000）
;   SECTORS    内核占几个扇区，构建时按产物大小算出来
%ifndef KERNEL_SEG
%define KERNEL_SEG 0x1000
%endif
%ifndef SECTORS
%define SECTORS 32
%endif

bits 16
org 0x7c00

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
    mov ch, 0
    mov cl, 2                  ; 从第 2 扇区开始
    mov dh, 0
    mov word [left], SECTORS

.read:                         ; 一次一个扇区：不跨轨、不赌 BIOS 的批量读
    mov ax, 0x0201
    mov dl, [drive]
    int 0x13
    jc  disk_error
    dec word [left]
    jz  .loaded
    add bx, 512                ; 满 64K 就抬 512 个段，es:bx 始终跟着走
    jnc .next
    mov ax, es
    add ax, 0x20
    mov es, ax
.next:
    inc cl
    cmp cl, 19                 ; 一条轨 18 个扇区，到头换面，再到头换柱面
    jb  .read
    mov cl, 1
    xor dh, 1
    jnz .read
    inc ch
    jmp .read

.loaded:
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
left:    dw 0
message: db "disk error", 13, 10, 0

times 510-($-$$) db 0
dw 0xaa55
