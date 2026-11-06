# 关卡格式

一章一个目录：`assets/chapters/NN-name/`

| 文件 | 必需 | 说明 |
| --- | --- | --- |
| `note.md` | 是 | 正文。只写 Markdown，不写判定，不下结论 |
| `start.asm` | 是 | 打开本章时的初始源码 |
| `solution.asm` | 否 | 「看示例」载入的版本 |

## 约定

- 目录名 `NN-slug`，`NN` 两位数字，按字典序即章节序。
- `note.md` 首行是一级标题，即章节名。
- 源码只允许 `bits 16` / `org 0x7c00` 起步，末尾必须有 `times 510-($-$$) db 0` 与 `dw 0xaa55`。
- 装载时若 `start.asm` 缺失或无法汇编，章节仍显示正文，只是不能运行。
