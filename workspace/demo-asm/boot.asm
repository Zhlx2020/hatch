; 512 字节的演示：不写 C，只靠 BIOS 和两个端口。
;
; 上手顺序：
;   1. 点右上「运行」，屏幕会出现提示语。
;   2. 在行号那一列点一下就是断点，再运行会停在那行。
;   3. 右下角的寄存器、反汇编、内存跟着走，可以单步看每条指令。
;
; 键盘直接读 0x64 状态口和 0x60 数据口，绕过 BIOS，
; 所以松开位、扩展键都得自己判断——正好拿来练端口和扫描码。
bits 16
org 0x7c00

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7c00

    mov si, banner
    call puts

loop:
    in  al, 0x64                    ; 状态口：bit0 置位表示有键等你读
    test al, 1
    jz  loop

    in  al, 0x60                    ; 读走扫描码，别把缓冲区堵住
    cmp al, 0xe0                    ; 扩展键前缀，演示里先跳过
    je  loop
    test al, 0x80                   ; bit7 置位是松开，只处理按下
    jnz loop

    cmp al, 0x01                    ; Esc 结束
    je  bye

    call scancode                   ; 查表转 ASCII
    test al, al
    jz  loop
    mov ah, 0x0e                    ; BIOS 打字机输出
    int 0x10
    jmp loop

bye:
    mov si, parting
    call puts
.hang:
    hlt
    jmp .hang

; 打印以 0 结尾的字符串
puts:
    push ax
    push si
.next:
    lodsb
    test al, al
    jz .done
    mov ah, 0x0e
    int 0x10
    jmp .next
.done:
    pop si
    pop ax
    ret

; 扫描码转 ASCII：够敲字母数字就行，别的给 0
scancode:
    push bx
    mov bx, table
    xor ah, ah
    add bx, ax
    mov al, [bx]
    pop bx
    ret

table:
    db 0, 27, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 8
    db 9, 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', 13
    db 0, 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', 39, '`'
    db 0, 92, 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/'
    times 128 - ($ - table) db 0

banner:  db "OS LAB - asm boot demo", 13, 10, "Type something, Esc quits.", 13, 10, 0
parting: db 13, 10, "bye", 13, 10, 0

times 510-($-$$) db 0
dw 0xaa55
