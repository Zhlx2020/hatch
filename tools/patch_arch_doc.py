import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "docs/architecture.md"
s = p.read_text(encoding="utf-8")
s = s.replace("  services/     可复用能力（会话、组装、静态反汇编、串口、工作区）",
              "  services/     可复用能力（会话、组装/C 构建、行映射、静态反汇编、串口、工作区、配置）")
s = s.replace("""保存 → services.checker → nasm → 诊断行（编辑器标红）
组装 → nasm -l → services.sourcemap → 暂停时标记当前源码行""",
"""保存 → services.checker → nasm/cc → 诊断行（编辑器标红）
点行号 → services.linemap（nasm 列表或 objdump -dl）→ 地址 → gdb 断点
组装 → nasm -l 或 gcc+ld+objcopy → services.sourcemap → 暂停时标记当前源码行""")
s = s.replace("- 新主题：只动 `assets/ui/styles/`，颜色全走 `base.css` 变量。",
              "- 新主题：只动 `assets/ui/styles/`，颜色全走 `base.css` 变量。\n"
              "- 新语言：在 `services/build.py` 注册后缀并返回 `(镜像, 行映射)`；映射统一成 `路径 → {行: 地址}`。")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
