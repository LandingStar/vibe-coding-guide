# Commit Message（中文版）

```
release: 收口 v0.9.5 preview release surface 与打包一致性

完成 progress graph artifact consistency audit，并将 runtime、official instance、pack-manifest 与 release 文档统一收口到 0.9.5。补齐 release 流程中的 VSIX 构建与同步、stale 产物清理、Windows npm 解析与安装态 MCP 验证，确保预览发布产物、版本口径与安装路径保持一致。

## 变更

- 刷新真实 `.codex/progress-graph/latest.json`、`.dot`、`.html`，修复 safe stop 之后的 stale artifact 偏差，并复核 direction-candidates 当前状态与历史条目的一致性
- dual-package 版本面同步到 `0.9.5`，包括 runtime、instance、pack-manifest、官方实例 `__version__` / `runtime_compatibility` 与 release 文档
- release 文档与产物面同步收口：VS Code extension 版本口径统一到 `0.1.3`
- `scripts/release.py` 现在会读取 `vscode-extension/package.json` 当前版本、构建并同步 VSIX 到 `release/`，同时清理旧 wheel / VSIX，避免 release 目录残留旧批次产物
- Windows 下的扩展打包改为显式解析 `npm.cmd`，避免 Python subprocess 找不到 `npm`
- 保持交付边界不变：`doc-based-coding-v0.9.5.zip` 继续只包含双 wheel 与 release 文档，VSIX 单独分发

## 验证

- `pytest tests/test_progress_graph_doc_projection.py -q`：3 passed
- `pytest tests -v --tb=short`：1366 passed, 2 skipped
- `release/verify_version_consistency.py`：All versions consistent
- `scripts/release.py --no-isolation`：生成 `release/doc-based-coding-v0.9.5.zip`
- `scripts/release.py --skip-tests --no-isolation`：生成并同步 `release/doc-based-coding-0.1.3.vsix`
- 安装态验证：`doc-based-coding-mcp --help`、`doc-based-coding info`、`doc-based-coding validate`、`pytest tests/test_dual_package_distribution.py -q`（6 passed）
```
