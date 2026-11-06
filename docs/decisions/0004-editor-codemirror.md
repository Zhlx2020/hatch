# 0004 编辑器用 CodeMirror 6 自己打包

## 背景

需要语法高亮、补全、保存即校验、当前指令行标记。候选是 Monaco 和 CodeMirror 6。

| 项 | Monaco | CodeMirror 6 |
| --- | --- | --- |
| 体积 | 数 MB，含 worker | 打包后约 380 KB |
| 离线使用 | 需要 worker 目录与 AMD 装载 | 一个 ESM 文件即可 |
| 自定义语言 | Monarch 词法，配置面很大 | StreamLanguage 一个函数 |
| 16 位汇编适配 | 无现成语言，仍要自己写 | 同上，但代价小 |

## 决定

用 CodeMirror 6。词法、指令表、补全源、诊断接入都在本仓库里，`tools/editor_entry.js`
配合 `tools/build_editor.mjs`（esbuild）打成 `assets/ui/vendor/editor.bundle.js`，产物入库，
运行时不联网、不跑 node。

## 代价

- 改编辑器要重跑 `npm install` 与 `node tools/build_editor.mjs`，产物必须一并提交。
- 自带词法只覆盖 NASM 语法表层，不做语义分析；真正的判定交给 nasm 本身。

## 影响

- `assets/ui/vendor/editor.bundle.js` 是构建产物，允许进版本库。
- 诊断来自 `services/checker.py`（只在保存后跑，`.inc` 跳过），与运行互不影响。
- 当前指令行靠 `services/sourcemap.py` 从 nasm 列表映射地址，仅在暂停时标记。
