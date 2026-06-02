# doc-based-coding v0.9.7 Preview Release (2026-06-02)

本次 `v0.9.7` preview release 以外部 `knowledge-graph-engine` 接入和图谱发布边界收口为核心：VS Code progress graph preview 已从归档的 G6 路线切换为独立图谱组件驱动，并把运行时代码打入 VSIX，同时在 release zip 中保留固定 graph engine tarball 作为可复现构建材料。

## 打包内容

| 产物 | 版本 | 说明 |
|------|------|------|
| `doc_based_coding_runtime-0.9.7-py3-none-any.whl` | 0.9.7 | 平台运行时，包含 CLI、MCP server、PDP/PEP、workflow、pack runtime |
| `doc_loop_vibe_coding-0.9.7-py3-none-any.whl` | 0.9.7 | 官方 doc-loop 实例 pack |
| `doc-based-coding-0.2.0.vsix` | 0.2.0 | VS Code 扩展，内含已构建的 graph webview runtime |
| `vscode-extension/vendor/note-web-knowledge-graph-engine-0.1.0.tgz` | 0.1.0 | 固定 graph engine 构建输入，用于审计和可复现构建 |
| `doc-based-coding-v0.9.7.zip` | 0.9.7 批次 | 一体 release 包，包含上述 wheel、VSIX、构建输入与安装文档 |

## 本次版本重点

### 1. Knowledge Graph Engine 图谱接入

- VS Code progress graph preview 已接入外部 `@note-web/knowledge-graph-engine` 的 `GraphModel`、`SimulationClient` 与 `Canvas2DRenderer`
- 图谱支持缩放、平移、拖拽、标签覆盖率/大小、颜色组、邻域突出、节点大小策略与布局摇散入口
- `Shake Layout` 会短暂使用极端力参数加速打开拓扑，并在 refresh graph 后自动执行一次
- 旧 G6 路线已保留为归档参考，不再进入当前构建链路

### 2. 发布态图谱依赖固定

- VSIX 运行时不依赖用户机器上的 graph engine 工作区；webview renderer 与 worker 已由 esbuild 打包到 `dist/webviews`
- `vscode-extension/package.json` 已从开发态外部路径切换到 release-local tarball：`file:vendor/note-web-knowledge-graph-engine-0.1.0.tgz`
- release 检查会拒绝 graph engine 继续使用非 `vendor/` 的开发态 `file:` 依赖
- release zip 现在包含 VSIX 和 graph engine tarball，便于一体分发、审计和复现构建

### 3. 版本与包边界

- runtime、instance、pack-manifest 与 release 文档同步到 `0.9.7`
- VS Code extension 独立版本线推进到 `0.2.0`
- 当前标准固定为：组件独立 SemVer、宿主固定依赖、VSIX 自包含运行时制品

## 验证结果

- `python release/verify_version_consistency.py --skip-wheel-files`：通过
- `python scripts/build.py --no-isolation`：通过
- `npm run build`：通过
- `node --test dist/test/progressGraphPreviewHtml.test.js`：通过
- `node --test dist/test/progressGraphColorGroups.test.js`：通过
- `node --test dist/test/aiChatToolLoop.test.js`：通过
- `python scripts/release.py --skip-tests --no-isolation`：生成新的双 wheel、`release/doc-based-coding-v0.9.7.zip` 与 `release/doc-based-coding-0.2.0.vsix`

## 安装顺序

```bash
pip install --force-reinstall doc_based_coding_runtime-0.9.7-py3-none-any.whl
pip install --force-reinstall --no-deps doc_loop_vibe_coding-0.9.7-py3-none-any.whl
```

VS Code 扩展通过 "Install from VSIX" 安装 `doc-based-coding-0.2.0.vsix`。Graph engine 已内嵌在 VSIX 的 webview 构建产物中，用户不需要单独安装 npm 包或准备外部 graph engine 工作区。
