; setup.asm —— boot/setup.s 的 nasm 移植。
;
; 干的还是那些事：拿 BIOS 数据存到 0x90000、把 system 从 0x10000 搬到 0、装 GDT、
; 开 A20、重排 8259、进保护模式后跳到 0:0（也就是内核的 startup_32）。
;
; 原版末尾用 `.org 508` 之类靠的是 as86，这里用 times 补到 5 个扇区：第 5 个扇区是填充，
; 让内核正好从第 6 扇区开始——和原版 tools/build 的排布一致，bootsect 的 sread 起点也按这个写。

INITSEG  equ 0x9000
SETUPSEG equ 0x9020

bits 16
org 0

start:
    mov ax, INITSEG
    mov ds, ax

    mov ah, 0x03                ; 光标位置存到 0x90000，con_init 会来取
    xor bh, bh
    int 0x10
    mov [0], dx

    mov ah, 0x88                ; 扩展内存大小
    int 0x15
    mov [2], ax

    mov ah, 0x0f                ; 显卡信息
    int 0x10
    mov [4], bx
    mov [6], ax

    mov ah, 0x12                ; EGA/VGA 配置
    mov bl, 0x10
    int 0x10
    mov [8], ax
    mov [10], bx
    mov [12], cx

    ; BIOS 的 0x104/0x118 向量表 SeaBIOS 不填，只能自己用 int 13h 的 AH=08 问
    mov ax, INITSEG
    mov es, ax
    mov bx, 0x0080              ; hd0 参数表
    mov dl, 0x80
    xor bp, bp                  ; 0 = 主盘
    call get_hd_params
    mov ax, INITSEG
    mov es, ax
    mov bx, 0x0090              ; hd1 参数表
    mov dl, 0x81
    mov bp, 0x10                ; 0x10 = 从盘
    call get_hd_params


    cli

    mov ax, 0x0000              ; 把 system 搬到 0，一段一段来
    cld
do_move:
    mov es, ax
    add ax, 0x1000
    cmp ax, 0x9000
    jz end_move
    mov ds, ax
    xor di, di
    xor si, si
    mov cx, 0x8000
    rep movsw
    jmp do_move

end_move:
    mov ax, SETUPSEG
    mov ds, ax
    lidt [idt_48]
    lgdt [gdt_48]

    call empty_8042
    mov al, 0xd1
    out 0x64, al
    call empty_8042
    mov al, 0xdf                ; A20 on
    out 0x60, al
    call empty_8042

    mov al, 0x11                ; 8259 初始化，中断挪到 0x20 起
    out 0x20, al
    dw 0x00eb, 0x00eb
    out 0xa0, al
    dw 0x00eb, 0x00eb
    mov al, 0x20
    out 0x21, al
    dw 0x00eb, 0x00eb
    mov al, 0x28
    out 0xa1, al
    dw 0x00eb, 0x00eb
    mov al, 0x04
    out 0x21, al
    dw 0x00eb, 0x00eb
    mov al, 0x02
    out 0xa1, al
    dw 0x00eb, 0x00eb
    mov al, 0x01
    out 0x21, al
    dw 0x00eb, 0x00eb
    out 0xa1, al
    dw 0x00eb, 0x00eb
    mov al, 0xff
    out 0x21, al
    dw 0x00eb, 0x00eb
    out 0xa1, al
    dw 0x00eb, 0x00eb

    mov ax, 0x0001              ; 进保护模式
    lmsw ax
    jmp 8:0                     ; 内核 startup_32 在 0:0

; es:bx 收 16 字节硬盘参数（cyl, head, wpcom, ctl, lzone, sect）
get_hd_params:
    pusha
    push es
    push ds
    push es
    pop ds
    mov di, bx
    xor ax, ax
    mov cx, 8
    rep stosw                   ; 先清 16 字节
    mov ah, 0x08
    int 0x13
    jc .out
    mov di, bx
    mov ax, cx                  ; cyl 的高 2 位在 cl 的 6-7，接到 ch 上
    and ax, 0xc000
    mov al, ah
    mov ah, ch
    mov [di], ax                ; cyl
    mov [di+2], dh              ; heads
    mov al, cl
    and al, 0x3f
    mov [di+14], al             ; sect
    mov [di+8], bp              ; ctl
.out:
    pop ds
    pop es
    popa
    ret


empty_8042:
    dw 0x00eb, 0x00eb
    in al, 0x64
    test al, 2
    jnz empty_8042
    ret

gdt:
    dw 0, 0, 0, 0               ; 空描述符
    dw 0x07ff, 0x0000, 0x9a00, 0x00c0
    dw 0x07ff, 0x0000, 0x9200, 0x00c0

idt_48:
    dw 0
    dd 0

gdt_48:
    dw 0x800
    dd 0x90200 + gdt            ; setup 被读在 0x9020:0，gdt 就在 0x90200 加上段内偏移

times 4 * 512 - ($ - $$) db 0   ; 第二级只占 4 个扇区
times 512 db 0                  ; 第 5 个扇区是填充，内核从第 6 扇区开始
