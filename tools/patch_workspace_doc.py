"""Keep the workspace doc in step with C support."""
import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "docs/workspace.md"
s = p.read_text(encoding="utf-8")
s = s.replace("| `.c` `.h` | 预留，尚未接入工具链 |",
              "| `.c` `.h` | C 源文件与头文件，必须位于带 `oslab.toml` 的工程目录里才能运行 |\n"
              "| `oslab.toml` | 工程清单：`kind`、`entry`、`sources`、`boot`、`link` |\n"
              "| `settings.toml` | 工作区根上的启动按钮与 QEMU 配置，界面可改 |")
s = s.replace("- 只有 `.asm` 会走 `services/build.py` 的分派；新增语言只需注册新后缀，不动上层。",
              "- 运行入口先看清单：有 `oslab.toml` 就按它走，没有才把 `.asm` 当单文件工程。\n"
              "- 新增语言只需在 `services/build.py` 注册后缀并写一个处理函数，上层不动。")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
