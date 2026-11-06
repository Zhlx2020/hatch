import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

r = root / "README.md"
s = r.read_text(encoding="utf-8")
s = s.replace("- 看：VGA 画面与串口同屏，刷新浏览器不丢会话",
              "- 看：只有一块 VGA 画面；刷新浏览器不丢会话")
s = s.replace("## 硬约束", """## 串口去哪了

客户机往 COM1 写的文本仍被服务端收着，走 `GET /api/serial`（脚本与端到端测试用它断言客户机确实跑起来了），
但界面不再占格子：画面已经是文字的主出口，再放一份是重复。

## 硬约束""")
r.write_text(s, encoding="utf-8", newline="\n")

a = root / "docs/architecture.md"
t = a.read_text(encoding="utf-8")
t = t.replace("客户机 COM1 → chardev 5914 → services.serial → 面板（可回放）",
              "客户机 COM1 → chardev 5914 → services.serial → /api/serial（可回放，界面不显示）")
a.write_text(t, encoding="utf-8", newline="\n")
print("ok")
