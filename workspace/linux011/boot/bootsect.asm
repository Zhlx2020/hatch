; bootsect.asm —— boot/bootsect.s 的 nasm 移植，逐段对照，逻辑不动。
;
; 原版是 as86 语法，hatch 的两级引导用 nasm：这里只换语法，不改流程。
; 唯一多出来的一处是 setup 占 5 个扇区（原版 4 个），好让内核正好落在第 6 扇区，
; 和原版 build 工具的排布一致。
;
; SYSSIZE 是还能装多少（单位 16 字节）：0x3000 = 196,608 字节，超过就在 read_it
; 里读不到头。原版用它给内核封顶，这里留着同样的上限。
SYSSIZE equ 0x3000

SETUPLEN equ 4                  ; setup 的扇区数（原版就是 4）
BOOTSEG  equ 0x07c0
INITSEG  equ 0x9000             ; 把自己挪到这儿，让开 0x7c00
SETUPSEG equ 0x9020
SYSSEG   equ 0x1000             ; 内核先落在 0x10000，setup 会再搬去 0
ENDSEG   equ SYSSEG + SYSSIZE

ROOT_DEV equ 0x301              ; 第一块硬盘的第一分区；0x21D = 第二张软盘

bits 16
org 0x7c00

_start:
    mov ax, BOOTSEG
    mov ds, ax
    mov ax, INITSEG
    mov es, ax
    mov cx, 256
    xor si, si
    xor di, di
    cld
    rep movsw
    jmp INITSEG:(go - 0x7c00)   ; 段内偏移，不是 0x7c00 起的绝对地址

go:
    mov ax, INITSEG
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0xff00

load_setup:
    mov dx, 0x0000
    mov cx, 0x0002
    mov bx, 0x0200
    mov ax, 0x0200 + SETUPLEN
    int 0x13
    jnc ok_load_setup
    mov dx, 0x0000
    mov ax, 0x0000
    int 0x13
    jmp load_setup

ok_load_setup:
    mov dl, 0x00
    mov ax, 0x0800              ; 取磁盘参数：每道扇区数
    int 0x13
    mov ch, 0x00
    mov [sectors - 0x7c00], cx
    mov ax, INITSEG
    mov es, ax

    mov ah, 0x03                ; 读光标
    xor bh, bh
    int 0x10

    mov cx, 24
    mov bx, 0x0007
    mov bp, msg1 - 0x7c00
    mov ax, 0x1301
    int 0x10

    mov ax, SYSSEG
    mov es, ax
    call read_it
    call kill_motor

    mov ax, [root_dev - 0x7c00]
    test ax, ax
    jnz root_defined
    mov bx, [sectors - 0x7c00]
    mov ax, 0x0208              ; /dev/ps0 1.2M
    cmp bx, 15
    je root_defined
    mov ax, 0x021c              ; /dev/PS0 1.44M
    cmp bx, 18
    je root_defined
undef_root:
    jmp undef_root
root_defined:
    mov [root_dev - 0x7c00], ax
    jmp SETUPSEG:0

; 把 system 整段读到 0x10000 起，绝不跨 64K 边界
sread: dw 2 + SETUPLEN   ; 引导扇区 + 5 个 setup 扇区都在前面了
head:  dw 0
track: dw 0

read_it:
    mov ax, es
    test ax, 0x0fff
die:
    jnz die
    xor bx, bx
rp_read:
    mov ax, es
    cmp ax, ENDSEG
    jb ok1_read
    ret
ok1_read:
    mov ax, [sectors - 0x7c00]
    sub ax, [sread - 0x7c00]
    mov cx, ax
    shl cx, 9
    add cx, bx
    jnc ok2_read
    je ok2_read
    xor ax, ax
    sub ax, bx
    shr ax, 9
ok2_read:
    call read_track
    mov cx, ax
    add ax, [sread - 0x7c00]
    cmp ax, [sectors - 0x7c00]
    jne ok3_read
    mov ax, 1
    sub ax, [head - 0x7c00]
    jne ok4_read
    inc word [track - 0x7c00]
ok4_read:
    mov [head - 0x7c00], ax
    xor ax, ax
ok3_read:
    mov [sread - 0x7c00], ax
    shl cx, 9
    add bx, cx
    jnc rp_read
    mov ax, es
    add ax, 0x1000
    mov es, ax
    xor bx, bx
    jmp rp_read

read_track:
    push ax
    push bx
    push cx
    push dx
    mov dx, [track - 0x7c00]
    mov cx, [sread - 0x7c00]
    inc cx
    mov ch, dl
    mov dx, [head - 0x7c00]
    mov dh, dl
    mov dl, 0
    and dx, 0x0100
    mov ah, 2
    int 0x13
    jc bad_rt
    pop dx
    pop cx
    pop bx
    pop ax
    ret
bad_rt:
    mov ax, 0
    mov dx, 0
    int 0x13
    pop dx
    pop cx
    pop bx
    pop ax
    jmp read_track

kill_motor:
    push dx
    mov dx, 0x3f2
    mov al, 0
    out dx, al
    pop dx
    ret

sectors: dw 0
msg1: db 13, 10, "Loading system ...", 13, 10, 13, 10

times 508 - ($ - $$) db 0
root_dev: dw ROOT_DEV
dw 0xAA55
