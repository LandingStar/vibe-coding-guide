# Planning Gate: Driver / 实例包分离审查

- **日期**: 2026-04-13
- **状态**: COMPLETED
- **来源**: [design_docs/Project Master Checklist.md](../../Project%20Master%20Checklist.md) post-v1.0 待办（中高优先级）
- **权威参考**:
  - [design_docs/tooling/Dual-Package Distribution Standard.md](../tooling/Dual-Package%20Distribution%20Standard.md)
  - [docs/platform-positioning.md](../../docs/platform-positioning.md)
  - [docs/plugin-model.md](../../docs/plugin-model.md)

## 目标

审查当前仓库中 driver 核心代码（`src/`）、doc-loop 官方实例 pack 资产（`doc-loop-vibe-coding/`）与 release 产物（`release/`、`dist-verify*/`）的组织边界，输出分离审查报告，并推进必要的结构性修复。

## 审查结果摘要

### 总体评估: 大部分边界清晰，2 处需修复

| 维度 | 状态 | 备注 |
|------|------|------|
| 交叉导入 | ✅ 清晰 | `src/` 与 `doc-loop-vibe-coding/` 无交叉导入 |
| 包配置 | ✅ 清晰 | 两个 `pyproject.toml` 职责明确、依赖方向正确（instance → runtime） |
| CLI 入口 | ✅ 清晰 | runtime 入口 `doc-based-coding*`，instance 入口 `doc-loop-*` |
| 发布包结构 | ✅ 清晰 | `dist-verify/` 和 `dist-verify-instance/` 已完全分离 |
| 根级文件 | ✅ 清晰 | 均属仓库级开发文档或 runtime 配置 |
| `docs/` 权威文档 | ✅ 合理 | `official-instance-doc-loop.md` 定义平台对官方实例的契约，属于平台视角 |
| 测试组织 | ✅ 可接受 | `test_official_instance_e2e.py` 用硬编码路径测试集成，合理 |
| **运行时硬编码实例路径** | 🔴 **违规** | `src/workflow/external_skill_interaction.py` L41-44 |
| **references 放置** | 🟡 **待决** | `temporary-override.md` 放在实例包还是提升为平台文档 |

### 发现 1 (HIGH): 运行时硬编码实例路径

**位置**: `src/workflow/external_skill_interaction.py` 第 41-44 行

```python
_SHIPPED_COPY_FILES = [
    * _REFERENCE_IMPLEMENTATION_FILES,
    "doc-loop-vibe-coding/references/external-skill-interaction.md",
]
```

**问题**: runtime 代码不应假设任何特定实例包的文件路径。drift-check 的"哪些文件是 shipped copy"应由 pack manifest 声明，runtime 动态发现。

**修复方案 (Slice A)**:
1. 在 pack manifest 中增加 `shipped_copies` 声明字段（或复用 `always_on`），让实例包自己声明哪些文件是权威文档的副本
2. `build_external_skill_interaction_contract()` 从已加载的 pack context 中动态发现 shipped copies，而不是使用硬编码列表
3. 从 `_SHIPPED_COPY_FILES` 中移除硬编码实例路径；仅保留平台本体的 reference implementation 路径（这些是 `.github/skills/` 下的，属于 runtime 本体）
4. 更新测试确保 drift-check 仍正常工作

### 发现 2 (MEDIUM): temporary-override.md 放置位置

**位置**: `doc-loop-vibe-coding/references/temporary-override.md`

**问题**: 临时覆盖机制（`TemporaryOverride` 数据模型、`governance_override` MCP tool、约束分类）全部在 runtime 中实现。reference doc 描述的是平台通用能力，但当前放在实例包内。

**背景**: `references/` 目录下的其他文件（`workflow.md`、`conversation-progression.md`、`external-skill-interaction.md`、`subagent-delegation.md`）也存在同样的模式——它们描述的都是平台能力，但作为"实例 pack 的 always_on reference"提供给使用该实例的项目。

**待决选项**:
- **A. 保持现状**: reference docs 作为 instance pack 的 always_on 内容，实例包负责把平台概念翻译成用户可消费的 reference。这与 `plugin-model.md` 中"pack 可以包含引导内容"一致。
- **B. 提升到 docs/**: 把 `temporary-override.md` 移到 `docs/` 中作为独立权威文档，实例 reference 改为指向平台权威。但这可能过度拆分，且需改 `pack-manifest.json` 和 `project-local.pack.json`。

## 实施切片

### Slice A: 消除运行时硬编码实例路径

**范围**:
1. `src/workflow/external_skill_interaction.py`: 拆分 `_SHIPPED_COPY_FILES` 为平台本体路径（保留）+ pack-declared 路径（动态发现）
2. `build_external_skill_interaction_contract()`: 接受 pack context 参数，从中提取 shipped copies
3. 调用方适配（`src/workflow/pipeline.py` 或 `src/mcp/tools.py` 中调用 `build_external_skill_interaction_contract` 的地方）
4. 测试更新

**产出**: runtime 不再包含任何实例特定路径。

### Slice B (已决): reference doc 放置策略

用户决定：保持现状。reference docs 留在实例包 `doc-loop-vibe-coding/references/`，作为面向消费者的 always_on 参考内容。理由：
- Reference docs 不是权威源副本，而是实例包自包含的简化参考
- 安装态下实例包无法依赖平台包的 `docs/` 目录
- 5 个 reference docs 的放置模式保持一致

## 验证项

- [x] `src/` 中不再包含 `doc-loop-vibe-coding` 字面路径
- [x] drift-check 功能通过 pack context 动态发现 shipped copies
- [x] 全量测试通过（651 passed, 2 skipped, 1 pre-existing failure）
- [ ] 若调整 reference 放置，pack-manifest.json 和 project-local.pack.json 保持一致

## 风险

| 风险 | 严重性 | 缓解 |
|------|--------|------|
| drift-check 发现逻辑变更导致功能退化 | 中 | 现有测试覆盖 drift-check 行为 |
| 过度设计 pack manifest 的 shipped_copies 字段 | 低 | 尽量复用现有 manifest 字段 |
