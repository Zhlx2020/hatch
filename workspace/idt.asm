BITS 16
ORG 0x7C00

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    call serial_init
    lgdt [gdt_desc]
    mov eax, cr0
    or eax, 1
    mov cr0, eax
    jmp 0x08:pm_entry

BITS 32
pm_entry:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov esp, 0x90000
    call cls32

    mov eax, handler
    mov word [idt + 3*8 + 0], ax
    shr eax, 16
    mov word [idt + 3*8 + 6], ax
    mov word [idt + 3*8 + 2], 0x08
    mov byte [idt + 3*8 + 4], 0
    mov byte [idt + 3*8 + 5], 0x8E

    lidt [idt_desc]

    int 3

    jmp $

handler:
    mov esi, msg32
.next:
    lodsb
    test al, al
    jz .done
    call putc32
    jmp .next
.done:
    jmp $

cls32:                      ; 清屏
    push eax
    push ecx
    push edi
    mov edi, 0xB8000
    mov ecx, 2000
    mov eax, 0x0A200A20
    rep stosd
    mov dword [cursor32], 0
    pop edi
    pop ecx
    pop eax
    ret

putc32:                     ; al = 字符：串口 + VGA 双写
    push eax
    push bx
    push dx
    push edi
    cmp al, 10
    je .newline
    cmp al, 13
    je .done
    mov ah, al
.wait:
    mov dx, 0x3FD
    in al, dx
    test al, 0x20
    jz .wait
    mov dx, 0x3F8
    mov al, ah
    out dx, al
    mov edi, [cursor32]
    add edi, 0xB8000
    mov ah, 0x0A
    mov [edi], ax
    add dword [cursor32], 2
    jmp .done
.newline:
    mov eax, [cursor32]
    xor edx, edx
    mov ebx, 160
    div ebx
    inc eax
    mul ebx
    cmp eax, 4000
    jb .store
    xor eax, eax
.store:
    mov [cursor32], eax
.done:
    pop edi
    pop dx
    pop bx
    pop eax
    ret

cursor32: dd 0

BITS 16
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

gdt:
    dq 0
    dw 0xFFFF, 0
    db 0, 0x9A, 0xCF, 0
    dw 0xFFFF, 0
    db 0, 0x92, 0xCF, 0
gdt_end:

gdt_desc:
    dw gdt_end - gdt - 1
    dd gdt

align 8
idt: times 8*8 db 0
idt_end:

idt_desc:
    dw idt_end - idt - 1
    dd idt

msg32: db "FAULT 3 CAUGHT", 13, 10, 0

times 510-($-$$) db 0
dw 0xAA55
