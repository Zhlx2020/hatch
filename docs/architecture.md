# 架构

## 分层

```
__main__        入口：serve / window，单实例锁与端口清理
  web/          只做 HTTP 与 WS 的接线，不含业务
    server.py   app 装配
    routes.py   路由表
    handlers.py 处理器
  services/     可复用能力（会话、组装、静态反汇编、串口、工作区）
  core/         仲裁器与状态：唯一状态机、唯一锁
  backend/      调试后端（协议在 base.py 之后）：qemu/ 默认，bochs/ 保留
  display/      画面来源（协议在 base.py 之后）：qemu 走 vnc.py
  assets/ui/    静态资源：styles/、js/、vendor/（编辑器打包产物）
```

依赖方向只能向下：`web → services → core → backend/display`。反向引用一律经由 `session.py` 注入。

## 铁律

1. 裸协议细节只出现在后端内部：gdb 帧在 `backend/qemu/rsp.py`，文本命令在 `backend/bochs/protocol.py`。其他地方调用 `adapter` 的方法。
2. 画面泵在服务启动时就独占一条上游连接，跟浏览器在不在无关；页面刷新只换订阅者。
3. 端口、帧间隔、状态栏尺寸等常量只在 `config.py`。端口固定，因此进程唯一：启动清残留，点运行先杀旧实例并等端口释放。
4. 组件之间不互相改 DOM：`js/screen.js` 只管道与画布，`js/input.js` 只键鼠，`js/panels.js` 只渲染面板。
5. 没有章节层：`workspace/` 里的文件就是全部工作单元，`services/` 不认识「课」这个概念。
6. 前端第三方库只以打包产物形式出现（`assets/ui/vendor/`），由 `tools/build_editor.mjs` 生成，运行时不联网。
7. 编辑器诊断走 `services/checker.py`，只读不改；它与运行路径完全分离，校验失败不影响在跑的机器。

## 数据流

```
键盘/鼠标 → ws → display.vnc → QEMU 5901
QEMU 5901 → display.vnc（原样转发 32bpp）→ ws → 画布（BGRX→RGBA 在客户端）
按钮 → services.session → core.arbiter → backend.qemu.adapter → gdb 5913
客户机 COM1 → chardev 5914 → services.serial → 面板（可回放）
保存 → services.checker → nasm → 诊断行（编辑器标红）
组装 → nasm -l → services.sourcemap → 暂停时标记当前源码行
```

## 为什么不用 Bochs 的调试器

Bochs 的调试器跑在 stdio 上，客户机运行时命令排队、CTRL_C/CTRL_BREAK 都打不断，
只能停机读状态；它的 rfb 只有 8bpp 3-3-2、端口写死 5900、只允许一个客户端。
QEMU 的 gdb stub 一个 `0x03` 字节就能异步中断，VNC 原生 32bpp、可指定端口、多客户端。
详见 `docs/decisions/0003-qemu-backend.md`。

## 扩展

- 新后端：实现 `backend/base.py` 的协议，在 `session.py` 注册，跑同一批 e2e。
- 新画面源：实现 `display/base.py`，选择由 `config.py` 决定。
- 新主题：只动 `assets/ui/styles/`，颜色全走 `base.css` 变量。
