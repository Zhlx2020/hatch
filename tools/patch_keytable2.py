import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "workspace/keyboard.asm"
s = p.read_text(encoding="utf-8")

old = '''scancode:                 ; al = 扫描码 -> al = 字符
    mov bx, table
    cmp al, 0x39
    ja .none
    xlatb
    ret
.none:
    xor al, al
    ret'''

new = '''scancode:                 ; al = 扫描码 -> al = 字符
    cmp al, 0x39          ; 空格
    jne .enter
    mov al, ' '
    ret
.enter:
    cmp al, 0x1C          ; 回车
    jne .index
    mov al, 13
    ret
.index:
    cmp al, 0x38
    ja .none
    mov bx, table
    xlatb
    ret
.none:
    xor al, al
    ret'''

assert old in s
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
