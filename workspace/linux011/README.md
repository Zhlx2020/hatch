# linux 0.11：真内核实验工程

这不是模拟器里的假 0.11，是 1991 年那份内核，用 hatch 编译、写进引导软盘、在 QEMU 里跑起来，
再到 `fork` / `execve` / `mount_root` / `/etc/rc` / `sh` 一路进用户态。`oslab.toml` 里
`stages` 是两级引导（0 号扇区引导块 → 1–5 扇区 setup），`kernel = 0x0` 是内核加载地址，
`symbol = "startup_32"` 是 head.s 里的入口——这些开关一改，就能照原样把内核搬到别处。

## 怎么跑

1. 打开 `init/main.c`，点「运行」。hatch 会用 w64devkit 编内核、拼引导软盘、启 QEMU。
2. `-S` 会让机器停在 0xFFF0，点「继续」才是真开机。
3. 内核打印 `Partition table ok.`、`Free mem:` 之后会挂上 B 盘（`rootfs/out/root.img`），
   执行 `/etc/rc`，给你一个 `hatch$` 提示符。能试的命令：`ls`、`cat hello.txt`、`cat /etc/rc`、
   `cd dev ; ls`、`clear`、`exit`。

改了 `rootfs/` 下的东西（`sh.c`、`rc`、`hello.txt`）要重新造盘，hatch 不会自动做：

```
set TEMP=.work\tmp & set TMP=.work\tmp        # Windows 的临时目录权限时好时坏
set PYTHONPATH=src
python workspace\linux011\rootfs\mkroot.py workspace\linux011\rootfs\out\root.img
```

`mkroot.py` 自己编 `crt.s` + `sh.c`（gcc/as/ld/objcopy 一条链，产物是 ZMAGIC a.out），
然后按 minix v1 拼文件系统、写分区表。控制台是 1980 年代的 VGA 字体，只认 ASCII，
所以 `/etc/rc` 用英文写，中文注释留在源码里。

## 为跑起来打的补丁

原树是 karottc/linux-0.11（1991 年原始代码）。要它在今天的内核编译器和 QEMU 11 上跑，
不得不动下面这些地方，每一处都写清了为什么：

| 位置 | 改动 | 原因 |
| --- | --- | --- |
| `boot/bootsect.asm`、`boot/setup.asm` | 原 as86 语法逐行改写成 NASM，流程不动 | 现在没有 as86 |
| `kernel/asm.s`、`boot/*.s` 等 | 行尾 `\ // 注释`、`_set_tssldt_desc` 等改内联汇编 | gas 不认 1991 年的写法 |
| `include/asm/system.h` | `move_to_user_mode` 里 `orl $0x3000,(%%esp)`（IOPL=3） | 用户态要用 `inb/outb` 探端口，没有 IOPL 就是 #GP |
| `include/asm/io.h` | 补 `outl/inl` | PCI 配置空间必须 4 字节访问，字节写会被静默丢掉 |
| `kernel/blk_drv/hd.c` | 加 `hatch_pci_ide_compat()`，`hd_init` 里第一个调；`reset_controller` 之后重选主盘 | QEMU 11 的 PIIX3 以 native 模式起来（prog-if 0x80、BAR 全 0），0.11 只会摸 0x1F0 那套 legacy 端口，不把 BAR/prog-if 改回来，硬盘状态永远读 0x00 |
| `kernel/blk_drv/hd.c` | 选盘写 `0xA0`（`HD_CURRENT`） | 不选盘时 ATA 状态寄存器就一直是 0，连 IDENTIFY 都不回 |
| `mm/memory.c` | 加 `hatch_copy_shared_page()`，`fork` 里等用户栈落实后调一次 | `fork` 在用户态发起时父子共用栈页，子进程一压栈就把父的栈改坏，init 根本进不去 |
| `kernel/printk.c` | `-DHATCH_SERIAL` 时把 printk 顺手镜像到 COM1 | 没显示器也能看内核串口日志 |
| `fs/exec.c` | 只认 ZMAGIC，`cld` 后 `copy_strings` | PE 目标下方向标志不可靠，`rep movsl` 会倒着拷字符串 |
| `kernel/exit.c`、`fork.c`、`tty_io.c` 等 | 杂项：`do_exit` 记录、`sleep_if_empty` 用 `current->signal` 判醒 | 老代码假定不会被打断，一有信号就死循环 |

## 磁盘上的东西

`rootfs/mkroot.py` 造的是 8 MB 盘：0 号扇区 MBR + 64 号扇区起的 minix 分区，
根目录里 `etc/rc`、`bin/sh`、`dev/tty0..2`、`hello.txt`。设备号按 0.11 的字符设备表来：
tty 是主号 4，写成 `0o2000` 这种“主号<<8|次号”，写成 `0o400` 会变成 `/dev/mem`，
读一下就返回 -EIO。

`bin/sh` 是这里自己写的（没有 libc，只有 `int 0x80`）：`cd/pwd/echo/cat/ls/clear/exit` 内建，
别的一律 `/bin/` 补路径再 `fork`+`execve`。`crt.s` 负责 argc/argv 和 `_exit`，
两个 `memcpy/memset` 供 gcc 生成的代码用。

## 已知没收拾的

- `hd_info[0].cyl` 读出来是 3584（BIOS 表 0x90080 的字序没按 word 拆），小盘够用，应该修。
- 开机早期有一行 `Unexpected HD interrupt`（0x91 WIN_SPECIFY 时 `intr_addr` 还没挂），无害。
- 用户态屏幕标记只有父进程写得出来（子进程 LDT 是 0x38、基址 0x4000000），串口和 printk 到处都能用。
