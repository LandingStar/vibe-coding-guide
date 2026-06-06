# Commit Message（中文）

```text
release: 打包 v0.9.8 preview release

将当前 Local Work Trajectory 与宿主协同相关成果收口到新的 preview release
批次：runtime 与 official instance 提升到 0.9.8，VS Code extension 提升到
0.2.1，继续固定 graph component 依赖边界，并将 secret hygiene 检查接入发布流程。

## 变更

- 新增 Local Work Trajectory MCP 生命周期接口与 React Flow / ELK UI
- 支持多线轨迹中的开线、merge/fan-in 与辅助关系展示
- 对齐文档与生成提示词，使 Codex 继续作为主要支持宿主链路
- 新增 secret scanner 与 Secret Hygiene / Log Redaction 标准
- 保持 VSIX graph runtime 自包含，并继续携带固定 graph engine tarball
- 刷新包版本、release 文档与 official instance pack lock

## 验证

- `python release/verify_version_consistency.py`：通过
- `python scripts/scan_secrets.py --scope worktree`：通过
- `python -m pytest tests/test_doc_loop_prompts.py tests/test_error_recovery.py::TestPipelineInitResilience::test_no_warnings_when_all_packs_valid -q`：3 passed
- `python scripts/release.py --no-isolation`：构建双 wheel，运行全量 pytest（`1432 passed, 3 skipped`），打包 `doc-based-coding-0.2.1.vsix`，并生成 `release/doc-based-coding-v0.9.8.zip`
```
