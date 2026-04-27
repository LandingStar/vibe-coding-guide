# doc-based-coding v0.9.5 Preview Release (2026-04-27)

本次 `v0.9.5` preview release 不只是最后一层发布补丁，而是把一整条 release 主线收口到同一批产物里：progress graph artifact consistency audit、dual-package 版本面对齐、release 流程硬化、VSIX 分离交付同步，以及安装态 MCP 验证都在这一版完成。

## 打包内容

| 产物 | 版本 | 说明 |
|------|------|------|
| `doc_based_coding_runtime-0.9.5-py3-none-any.whl` | 0.9.5 | 平台运行时，包含 CLI、MCP server、PDP/PEP、workflow、pack runtime |
| `doc_loop_vibe_coding-0.9.5-py3-none-any.whl` | 0.9.5 | 官方 doc-loop 实例 pack |
| `doc-based-coding-0.1.3.vsix` | 0.1.3 | VS Code 扩展，单独分发 |
| `doc-based-coding-v0.9.5.zip` | 0.9.5 批次 | 保持仅包含双 wheel 与 release 文档，不内嵌 VSIX |

## 本次版本重点

### 1. Progress graph artifact consistency audit 收口

- 重新生成 `.codex/progress-graph/latest.json`、`.dot`、`.html`，消除 recency semantics safe stop 之后的 stale artifact 偏差
- 复核 older plain lettered direction-candidate entries、latest numbered section 与当前 source docs 的状态一致性
- 保持当前 projection 边界稳定：`direction-candidates-global` 当前仍只投影候选 section，companion prose 继续留在后续切片

### 2. 0.9.5 双包版本面收口

- runtime、instance、pack-manifest 与 release 文档统一同步到 `0.9.5`
- 官方实例 `__version__` 与 `runtime_compatibility` 约束同步到当前 release 批次
- release 文档与安装面一并收口，VS Code extension 版本口径统一修正到 `0.1.3`

### 3. Release tooling 与扩展交付硬化

- 保持 VSIX 与 release zip 分离，不把扩展包重新塞回 `doc-based-coding-v0.9.5.zip`
- `scripts/release.py` 现在会读取 `vscode-extension/package.json` 的当前版本，构建并同步 `doc-based-coding-0.1.3.vsix` 到 `release/`
- release 流程会清理 `release/` 中旧批次的 wheel / VSIX，避免 stale 产物继续污染当前 release surface
- Windows 下的扩展打包改为显式解析 `npm.cmd`，避免 Python subprocess 找不到 npm 导致 VSIX 打包失败
- release 目录中的旧 `doc-based-coding-0.1.2.vsix` 已替换为当前 `doc-based-coding-0.1.3.vsix`

### 4. 安装态 MCP 验证补齐

- 在 `.venv-release-test` 中从 `release/` 目录强制重装 runtime 与 instance 两个 wheel
- 确认安装后的 `doc-based-coding-mcp` 入口可直接输出帮助信息，而不是继续依赖开发态源码入口
- 复核 `doc-based-coding info` / `doc-based-coding validate` 在当前仓库内均可正常工作
- 用 `tests/test_dual_package_distribution.py` 再次确认双包分发、入口点与实例兼容约束没有被 release 过程破坏

## 验证结果

- `pytest tests/test_progress_graph_doc_projection.py -q`：3 passed
- `pytest tests -v --tb=short`：1366 passed, 2 skipped
- `release/verify_version_consistency.py`：All versions consistent
- `scripts/release.py --no-isolation`：双 wheel 与 `doc-based-coding-v0.9.5.zip` 打包完成
- `scripts/release.py --skip-tests --no-isolation`：已构建并同步 `doc-based-coding-0.1.3.vsix` 到 `release/`
- `doc-based-coding-mcp --help`：OK，正常输出安装态 server 参数
- `doc-based-coding info`：OK，识别 `doc-loop-vibe-coding 0.9.5` 与当前项目本地 pack
- `doc-based-coding validate`：OK，返回 `passed`，无治理阻塞
- `pytest tests/test_dual_package_distribution.py -q`：6 passed

## 安装顺序

```bash
pip install doc_based_coding_runtime-0.9.5-py3-none-any.whl
pip install doc_loop_vibe_coding-0.9.5-py3-none-any.whl
```

VS Code 扩展继续通过 "Install from VSIX" 安装 `doc-based-coding-0.1.3.vsix`。

完整变更历史见仓库根目录 `CHANGELOG.md`。
