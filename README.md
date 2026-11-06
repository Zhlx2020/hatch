# OS Lab

在本地窗口里写引导扇区、起机器、下断点、看画面与串口。这是一台工作站，不是教程播放器。

- 写：编辑器直接改 `workspace/*.asm`，`nasm -f bin` 组装，512 字节扇区带 `0xAA55`
- 起：QEMU 无窗口启动，画面走 VNC 32bpp，调试走 gdb 远程协议
- 调：暂停、单步、继续、断点、寄存器、内存、反汇编
- 看：VGA 画面与串口同屏，刷新浏览器不丢会话

## 运行

```
python -m oslab            # 开窗
python -m oslab --serve    # 只起服务，浏览器开 127.0.0.1:8799
```

依赖：`qemu-system-i386`、`nasm`、`pywebview`、`aiohttp`，路径集中在 `src/oslab/config.py`。

## 验收

```
python -m pytest tests/unit -q      # 单元：汇编、反汇编、状态机
python tests/e2e/selftest.py        # 端到端：起机、中断、断点、串口、单实例
```

两项都必须全绿才算可交付。

## 硬约束

- 只有一个模拟器实例：再次点「运行」会先杀旧进程并等端口释放，启动时也会清理残留
- 端口固定：gdb 5913、串口 5914、VNC 5901；实例锁 5912，冲突时不会起第二份
- 刷新浏览器不影响客户机：画面与串口都会重新接上并回放
- 键盘走 X11 keysym，连接时补发全键松开，避免刷新后按键卡住
- 不判题、不内置章节；`workspace/` 里的文件就是全部工作单元

## 目录

见 `docs/architecture.md`。不要往 `src/oslab/` 之外写产品代码。
