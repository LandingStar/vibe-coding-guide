# Commit Message（中文版）

```text
release: 打包 v0.9.7 preview release，固定图谱组件发布边界

将当前 Knowledge Graph Engine 接入收口到新的 preview release 批次：runtime 与 official instance 同步到 0.9.7，VS Code extension 提升到 0.2.0，并把 graph engine 从开发态外部路径固定为 release-local tarball。

## 变更

- VS Code progress graph preview 接入外部 `@note-web/knowledge-graph-engine`，替代已归档的 G6 路线
- VSIX 运行时自包含 graph webview renderer / worker，用户无需单独安装 graph engine npm 包
- `vscode-extension/package.json` 切换到 `file:vendor/note-web-knowledge-graph-engine-0.1.0.tgz`
- release zip 现在包含双 wheel、VSIX、graph engine tarball 与安装文档
- release 检查新增 graph engine 开发态 file 依赖拦截，并正确区分 runtime 批次号与 VSIX 独立版本线

## 验证

- `python release/verify_version_consistency.py --skip-wheel-files`：passed
- `python scripts/build.py --no-isolation`：passed
- `npm run build`：passed
- `node --test dist/test/progressGraphPreviewHtml.test.js`：passed
- `node --test dist/test/progressGraphColorGroups.test.js`：passed
- `node --test dist/test/aiChatToolLoop.test.js`：passed
- `python scripts/release.py --skip-tests --no-isolation`：生成 `release/doc-based-coding-v0.9.7.zip` 与 `release/doc-based-coding-0.2.0.vsix`
```
