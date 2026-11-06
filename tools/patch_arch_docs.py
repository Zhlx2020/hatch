import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "docs/architecture.md"
s = p.read_text(encoding="utf-8")

s = s.replace("  assets/ui/    静态资源，按 styles/ 与 js/ 拆开",
              "  assets/ui/    静态资源：styles/、js/、vendor/（编辑器打包产物）")
s = s.replace("""5. 没有章节层：`workspace/*.asm` 就是全部工作单元，`services/` 不认识「课」这个概念。""",
              """5. 没有章节层：`workspace/` 里的文件就是全部工作单元，`services/` 不认识「课」这个概念。
6. 前端第三方库只以打包产物形式出现（`assets/ui/vendor/`），由 `tools/build_editor.mjs` 生成，运行时不联网。
7. 编辑器诊断走 `services/checker.py`，只读不改；它与运行路径完全分离，校验失败不影响在跑的机器。""")
s = s.replace("""按钮 → services.session → core.arbiter → backend.qemu.adapter → gdb 5913
客户机 COM1 → chardev 5914 → services.serial → 面板（可回放）""",
              """按钮 → services.session → core.arbiter → backend.qemu.adapter → gdb 5913
客户机 COM1 → chardev 5914 → services.serial → 面板（可回放）
保存 → services.checker → nasm → 诊断行（编辑器标红）
组装 → nasm -l → services.sourcemap → 暂停时标记当前源码行""")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
