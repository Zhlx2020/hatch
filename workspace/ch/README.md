# 两级引导链样例

`oslab.toml` 里 `stages` 列出两级，构建按顺序把它们摆到 0 号和 1–4 号扇区。

- `boot.asm`：0 号扇区，512 字节，把 `setup.asm` 读到 `0x9000` 然后跳过去。
- `setup.asm`：被读到 `0x9000`，往显存写一行字后停机。

跑起来画面上能看到 `stage 2 running from 0x9000`。按 `Ctrl+Y`（或点「看磁盘布局」）能看到两级各自的扇区范围。

要往真内核走：`kind` 改成 `"c"`，补 `sources`、`link`、`kernel`，把 `setup.asm` 里写显存那段换成读盘 + 开 A20 + 进保护模式，内核由它自己搬。
