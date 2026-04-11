# Planning Gate — Post-v1.0 Compatibility Metadata And Version Declaration

- Status: **COMPLETED**
- Date: 2026-04-11

## 问题陈述

双发行包最小安装骨架和官方实例 validator/script 边界都已收口，但 runtime 包与官方实例包之间仍缺少统一的机器可读兼容声明：

1. 官方实例包当前只在 Python 包依赖层声明 `doc-based-coding-runtime>=1.0.0,<2.0.0`。
2. pack 语义层还没有一个明确字段表达“这个官方实例面向哪个 runtime 语义范围设计”。
3. `design_docs/tooling/Dual-Package Distribution Standard.md` 已要求兼容关系同时在发行包元数据层和 pack/实例语义层表达，但当前只落了一半。

## 审核后边界

用户已确认：下一切片优先做“兼容元数据与版本声明”，暂不处理 MCP pack info 刷新一致性。

本轮边界固定为：

- 只定义并落地最小机器可读兼容声明
- 同时覆盖发行包元数据层与 pack/实例语义层
- 不在本轮设计完整版本矩阵或复杂求解算法
- 不在本轮扩展到 registry / marketplace / 自动化发布流程

## 权威输入

- `design_docs/tooling/Dual-Package Distribution Standard.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `docs/pack-manifest.md`
- `docs/project-adoption.md`
- `pyproject.toml`
- `doc-loop-vibe-coding/pyproject.toml`
- `doc-loop-vibe-coding/pack-manifest.json`
- `src/pack/manifest_loader.py`

## 本轮只做什么

### Slice A: 兼容声明字段定型

- 为 pack/实例语义层选择一个最小兼容字段。
- 明确该字段表达的是 runtime 兼容范围，而不是一般依赖列表。

### Slice B: 运行时与官方实例元数据落地

- 在官方实例包元数据层保留 runtime 依赖范围。
- 在官方实例 pack manifest 中补齐语义层兼容声明。
- 让 manifest loader 能稳定读取该字段。

### Slice C: 文档与验证对齐

- 在权威文档中记录该字段的职责边界。
- 增加 targeted tests，确保该兼容声明能被加载且与当前包元数据一致。

## 本轮明确不做什么

- 不做完整 semver 求解器
- 不实现多实例兼容冲突求解
- 不引入新的远端分发协议
- 不处理 MCP pack info 刷新一致性问题

## 验收与验证门

- pack/实例语义层存在明确的 runtime 兼容声明
- 官方实例包元数据层与 pack manifest 兼容范围一致
- manifest loader 能读取该字段
- 相关 targeted tests 通过

## 执行结果

- `src/pack/manifest_loader.py` 已新增 `runtime_compatibility` 字段支持。
- `doc-loop-vibe-coding/pack-manifest.json` 已声明 `runtime_compatibility: ">=1.0.0,<2.0.0"`。
- `doc-loop-vibe-coding/pyproject.toml` 的 runtime 依赖范围与 manifest 兼容字段已建立一一对应。
- `doc-loop-vibe-coding/scripts/validate_instance_pack.py` 现在会校验 `runtime_compatibility` 是否存在，且是否与 `pyproject.toml` 依赖范围一致。
- `docs/pack-manifest.md` 与 `design_docs/tooling/Dual-Package Distribution Standard.md` 已记录 `runtime_compatibility` 的职责边界。
- targeted tests 与官方实例自检均已通过。

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `.codex/checkpoints/latest.md`
- `docs/pack-manifest.md`
- `design_docs/tooling/Dual-Package Distribution Standard.md`

## 收口判断

- 当兼容声明字段、官方实例元数据、加载逻辑、文档与测试都完成对齐时，本切片即可收口。