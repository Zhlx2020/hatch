import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "README.md"
s = p.read_text(encoding="utf-8")

s = s.replace('''- 写：CodeMirror 6 编辑器，NASM 高亮、指令/寄存器/标签补全、保存即校验并标行''',
'''- 写：CodeMirror 6 编辑器，NASM/C 高亮、补全、保存即校验并标行；点行号就是断点''')
s = s.replace('''- 看：只有一块 VGA 画面；刷新浏览器不丢会话''',
'''- 语言：汇编直接编；C 走 32 位内核模板（引导扇区 + 链接脚本 + 行号映射）
- 看：只有一块 VGA 画面；刷新浏览器不丢会话''')

s = s.replace('''## 验收''', '''## 工程清单

带运行含义的目录放一份 `oslab.toml`：

```toml
kind = "c"                                  # c | asm
entry = "src/kmain.c"
sources = ["src/kmain.c", "src/screen.c"]
boot = "boot/boot.asm"                      # 16 位引导扇区
link = "boot/kernel.ld"
```

没有清单的裸 `.asm` 仍按单文件汇编运行。清单在 `services/project.py` 里校验，
缺项、类型错、文件不存在都会直说。

新建文件按钮里可以选「从模板新建」，自带 `asm-hello` 与 `c-hello` 两套。

## 断点

在编辑器点行号出红点，再点运行：服务端构建完立刻按行号解析地址、写好断点才放行，
不会跑过头。红色打点、行高亮、寄存器里的 `eip` 都对得上；点第二下取消。
构建后映射会更新，旧红点自动重算。

## 启动按钮与 QEMU

顶栏「设置」里能改按钮文字、悬停提示、点击行为（构建并运行 / 只构建）、是否停在入口，
以及内存、机器类型、CPU、白名单附加参数。配置落在 `workspace/settings.toml`，
保存前校验（不认识或已被托管的参数会拒绝），重启会话后生效。

## 验收''')

s = s.replace('''python -m pytest tests/unit -q      # 单元：工作区、汇编、反汇编、源映射、状态机、校验
python tests/e2e/selftest.py        # 端到端：目录 CRUD、起机、中断、断点、监视面、串口、单实例''',
'''python -m pytest tests/unit -q      # 单元：工作区、汇编、C 构建、行映射、反汇编、配置、校验
python tests/e2e/selftest.py        # 端到端：目录 CRUD、起机、断点（含 C 行断点）、模板、配置、串口、单实例''')

s = s.replace('''- 只有 `.asm` 能运行，其余后缀等工具链接入后由 `services/build.py` 注册''',
'''- 只有 `.asm` 与带清单的 `.c` 能运行，其余后缀由 `services/build.py` 拒绝并说明
- C 工具链默认用 `.work/w64/w64devkit/bin` 的 `gcc/ld/objcopy`，路径在 `config.py`''')

s = s.replace('''- `docs/decisions/` 逐条决策记录''', '''- `docs/c.md` C 工程怎么构成、怎么编、断点怎么落地
- `docs/decisions/` 逐条决策记录''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
