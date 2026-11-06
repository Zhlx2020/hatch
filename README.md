# OS Lab

在本地窗口里写引导扇区、起机器、下断点、看画面与串口。这是一台工作站，不是教程播放器。

- 写：CodeMirror 6 编辑器，NASM 高亮、指令/寄存器/标签补全、保存即校验并标行
- 组织：左栏是资源管理器，任意层级目录、右键新建改名删除、拖拽移动
- 起：QEMU 无窗口启动，画面走 VNC 32bpp，调试走 gdb 远程协议
- 调：暂停、单步、越过、运行到光标、断点、寄存器（可写、按位、按宽度）、内存任意地址、反汇编任意地址
- 看：只有一块 VGA 画面；刷新浏览器不丢会话

## 运行

```
python -m oslab            # 开窗
python -m oslab --serve    # 只起服务，浏览器开 127.0.0.1:8799
```

依赖：`qemu-system-i386`、`nasm`、`pywebview`、`aiohttp`，路径集中在 `src/oslab/config.py`。

## 验收

```
python -m pytest tests/unit -q      # 单元：工作区、汇编、反汇编、源映射、状态机、校验
python tests/e2e/selftest.py        # 端到端：目录 CRUD、起机、中断、断点、监视面、串口、单实例
```

两项都必须全绿才算可交付。

## 改前端

编辑器是打包产物，改了 `tools/editor_entry.js` 或词表后：

```
npm install
node tools/build_editor.mjs
```

产物 `src/oslab/assets/ui/vendor/editor.bundle.js` 要一起提交。

## 串口去哪了

客户机往 COM1 写的文本仍被服务端收着，走 `GET /api/serial`（脚本与端到端测试用它断言客户机确实跑起来了），
但界面不再占格子：画面已经是文字的主出口，再放一份是重复。

## 硬约束

- 只有一个模拟器实例：再次点「运行」会先杀旧进程并等端口释放，启动时也会清理残留
- 端口固定：gdb 5913、串口 5914、VNC 5901；实例锁 5912，冲突时不会起第二份
- 刷新浏览器不影响客户机：画面与串口都会重新接上并回放
- 键盘走 X11 keysym，连接时补发全键松开，避免刷新后按键卡住
- 不判题、不内置章节；`workspace/` 里的文件就是全部工作单元
- 只有 `.asm` 能运行，其余后缀等工具链接入后由 `services/build.py` 注册

## 文档

- `docs/architecture.md` 分层与数据流
- `docs/workspace.md` 目录与文件规则
- `docs/decisions/` 逐条决策记录

不要往 `src/oslab/` 之外写产品代码。
