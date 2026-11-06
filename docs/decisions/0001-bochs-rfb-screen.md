# 0001 画面走 Bochs rfb + 自绘客户端

> 已被 `0003-qemu-backend.md` 取代：默认后端改为 QEMU，本文的 8bpp、裁剪与 5900 端口只对 Bochs 后端成立。

## 结论
Bochs 以 `display_library: rfb` 启动，服务端 5900；我们的服务把 8bpp 3-3-2 转成 RGBA、
裁掉 32px 顶栏与 20px 状态栏，经 WebSocket 送给自写 canvas 客户端。

## 备选与否决理由
- **QEMU `-vnc` + noVNC**：QEMU 路径要另装一套调试链；noVNC 实测接不住 Bochs 的流
  （Bochs 只支持 8bpp 且忽略 SetPixelFormat，noVNC 按其自身像素格式解码即错位）。
- **`screendump` 出图**：每帧一张图，编码开销与抖动都大。
- **读 `0xB8000` 自绘**：只覆盖文本模式，且要「采样即停」打断执行。保留为回退路径。

## 代价
- 8bpp 3-3-2，颜色有台阶（白偏灰），属固有限制。
- 端口固定 5900 且绑 `0.0.0.0`，必须单实例。
- Bochs 整屏重绘，带宽靠差分与降帧压。

## 位置
实现见 `src/oslab/display/rfb.py` 与 `src/oslab/display/codec.py`。
