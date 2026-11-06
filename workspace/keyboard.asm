BITS 16
ORG 0x7C00

; 行编辑回显：处理 Shift 大小写、Tab、退格、回车，同时写文本屏和串口。
start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00

    call serial_init
    call cls
    mov si, msg
    call puts

.loop:
    in al, 0x64
    test al, 1
    jz .loop
    in al, 0x60

    cmp al, 0x2A           ; 左 Shift 按下
    je .shift_on
    cmp al, 0x36           ; 右 Shift 按下
    je .shift_on
    cmp al, 0xAA
    je .shift_off
    cmp al, 0xB6
    je .shift_off
    test al, 0x80          ; 其余只处理按下
    jnz .loop

    cmp al, 0x0E           ; 退格
    je .back
    call scancode
    test al, al
    jz .loop
    call putc
    jmp .loop

.shift_on:
    mov byte [shift], 1
    jmp .loop
.shift_off:
    mov byte [shift], 0
    jmp .loop

.back:
    call backspace
    jmp .loop

scancode:                 ; al = 扫描码 -> al = 字符
    cmp al, 0x39          ; 空格
    jne .enter
    mov al, ' '
    ret
.enter:
    cmp al, 0x1C          ; 回车
    jne .tab
    mov al, 13
    ret
.tab:
    cmp al, 0x0F
    jne .index
    mov al, ' '
    ret
.index:
    cmp al, 0x38
    ja .none
    mov bx, table
    cmp byte [shift], 0
    je .pick
    add bx, 0x40
.pick:
    xlatb
    ret
.none:
    xor al, al
    ret

backspace:
    mov ax, [cursor]
    test ax, ax
    jz .end
    sub ax, 2
    mov [cursor], ax
    mov bx, 0xB800
    mov es, bx
    mov di, ax
    mov word [es:di], 0x0A20
.end:
    ret

puts:
    lodsb
    test al, al
    jz .end
    call putc
    jmp puts
.end:
    ret

cls:
    push ax
    push cx
    push di
    push es
    mov ax, 0xB800
    mov es, ax
    xor di, di
    mov cx, 2000
    mov ax, 0x0A20
    rep stosw
    mov word [cursor], 0
    pop es
    pop di
    pop cx
    pop ax
    ret

serial_init:
    mov dx, 0x3F9
    xor al, al
    out dx, al
    mov dx, 0x3FB
    mov al, 0x80
    out dx, al
    mov dx, 0x3F8
    mov al, 1
    out dx, al
    mov dx, 0x3F9
    xor al, al
    out dx, al
    mov dx, 0x3FB
    mov al, 0x03
    out dx, al
    mov dx, 0x3FA
    mov al, 0xC7
    out dx, al
    ret

putc:                     ; al = 字符
    push ax
    push bx
    push dx
    push es
    push di
    cmp al, 13
    je .newline
    mov ah, al
.wait:
    mov dx, 0x3FD
    in al, dx
    test al, 0x20
    jz .wait
    mov dx, 0x3F8
    mov al, ah
    out dx, al
    mov bx, 0xB800
    mov es, bx
    mov di, [cursor]
    mov ah, 0x0A
    mov [es:di], ax
    add di, 2
    mov [cursor], di
    jmp .done
.newline:
    call vnewline
.done:
    pop di
    pop es
    pop dx
    pop bx
    pop ax
    ret

vnewline:                 ; 串口和文本屏各换一行
    push ax
    push bx
    push dx
    mov dx, 0x3FD
.w1:
    in al, dx
    test al, 0x20
    jz .w1
    mov dx, 0x3F8
    mov al, 10
    out dx, al
    mov ax, [cursor]
    mov bx, 160
    xor dx, dx
    div bx
    inc ax
    mul bx
    cmp ax, 4000
    jb .store
    xor ax, ax
.store:
    mov [cursor], ax
    pop dx
    pop bx
    pop ax
    ret

shift: db 0
cursor: dw 0

table:                    ; 扫描码 0x00-0x3F：小写表，再偏移 0x40 的 Shift 表
    db 0, 0, "1234567890-=", 0, 0
    db "qwertyuiop[]", 0, 0
    db "asdfghjkl;'", "`"
    db 0, "\zxcvbnm,./"
    times (0x40 - ($ - table)) db 0   ; 精确补齐到 0x40，Shift 表从这里开始
    db 0, 0, "!@#$%^&*()_+", 0, 0
    db "QWERTYUIOP{}", 0, 0
    db 'ASDFGHJKL:"', "~"
    db 0, "|ZXCVBNM<>?"

msg: db "KEYBOARD ECHO - shift/tab/backspace work", 13, 10, 0

times 510-($-$$) db 0
dw 0xAA55
