# Direction Analysis — Dogfood Pipeline 接入 Workflow

> 日期：2026-04-16  
> 前置：`design_docs/direction-candidates-after-phase-35.md` → 候选 A 已完成  
> 触发：Phase 35 dogfood promotion-packet pipeline 已实现但尚未接入治理闭环

## 背景与当前状态

### 已完成

- `src/dogfood/` 4 个模块完整实现：models / evaluator / builder / dispatcher
- 18 项专项测试 + 全量基线 964 passed, 2 skipped
- 数据流已验证：`Evidence → Symptoms → evaluate_promotion() → build_issue_candidate() → assemble_feedback_packet() → dispatch_to_consumers()`
- 6 个消费者的字段裁剪矩阵已定义：direction-candidates / checklist / phase-map / checkpoint / handoff / planning-gate

### 缺口

| # | 缺口 | 影响 |
|---|------|------|
| G1 | `dispatch_to_consumers()` 产出 `ConsumerPayload`，但没有人消费它 | 反馈包无法实际流入目标文档 |
| G2 | MCP 层未暴露 dogfood pipeline 完整流 | agent 无法通过 MCP 调用从 evidence 到 feedback 的链路 |
| G3 | Checkpoint / safe-stop 不知道 dogfood feedback 存在 | 跨 session 丢失反馈状态 |
| G4 | Pipeline.process() 后处理未挂载 dogfood 钩子 | 治理链与反馈链是两条独立路径 |

## 候选切片

### 切片 A: MCP 暴露 dogfood 完整流（最窄）

**做什么**：在 `src/mcp/tools.py` 新增 1 个 MCP 工具，把 dogfood pipeline 的完整 4 步流暴露为单次调用。

**签名草案**：
```python
def promote_dogfood_evidence(
    symptoms: list[dict],        # symptom_id, symptom_summary, evidence_refs, ...
    existing_issues: list[str],  # 已有 issue_id 列表（用于 S2 去重）
    date: str,                   # 日期标签
) -> dict:
    # 1. evaluate_promotion
    # 2. build_issue_candidate for each PROMOTE
    # 3. assemble_feedback_packet
    # 4. dispatch_to_consumers
    # 返回: {promoted: [...], suppressed: [...], packet: {...}, payloads: {...}}
```

**不做**：不修改 Pipeline.process()、不持久化、不改 checkpoint。

**优势**：
- 最窄 scope，可独立测试
- agent 立即可用（通过 MCP 调用）
- 与 Pipeline 编排无耦合

**风险**：低。

### 切片 B: MCP 暴露 + Consumer 文档写回（中等）

**做什么**：切片 A + 实现 `ConsumerPayload` → 目标文档的写回逻辑。

**Consumer 写回范围**：

| Consumer | 目标文件 | 写回方式 |
|----------|---------|---------|
| direction-candidates | `design_docs/direction-candidates-after-phase-{N}.md` | 追加 "dogfood feedback" 小节 |
| checklist | `design_docs/Project Master Checklist.md` | 追加到活跃待办 |
| checkpoint | `.codex/checkpoints/latest.md` | 追加 dogfood_feedback 字段 |
| planning-gate | 当前 active gate（如果存在） | 追加 feedback 引用 |
| phase-map | `design_docs/Global Phase Map and Current Position.md` | 不自动写，仅 MCP 返回 |
| handoff | CURRENT.md | 不自动写，仅 MCP 返回 |

**不做**：不修改 Pipeline.process() 后处理。

**风险**：中等。写回逻辑需要处理文件格式解析和追加位置定位。

### 切片 C: MCP + 写回 + Pipeline 后处理挂载（完整）

**做什么**：切片 B + 在 `Pipeline.process()` 的后处理阶段挂载 dogfood feedback 生成逻辑。

**额外修改**：
- `Pipeline.process()` 结果中新增 `dogfood_feedback` 字段
- 如果 `PackContext.flags` 中有 `collect_dogfood_feedback`，自动从 audit events 中提取 symptoms
- Checkpoint 写入时自动包含 feedback 摘要

**风险**：中高。涉及 Pipeline 核心数据流变更，需要回归全量测试。

## AI 倾向判断

**推荐切片 A 作为第一步**，理由：

1. **最窄 scope**：只新增 1 个 MCP 工具 + 对应测试，不改变任何现有数据流
2. **立即可用**：agent 通过 MCP 调用即可跑完 evidence → feedback 全流程
3. **验证接口**：切片 A 完成后，实际使用中会暴露 consumer 写回的真实需求和格式问题
4. **为切片 B 铺路**：consumer 写回的正确行为应该先通过 A 的实际使用来定义，而不是提前设计

切片 B 在 A 完成并实际使用后再做方向分析。切片 C 更远期。

## 切片 A 的窄边界

### 输入

- `symptoms: list[dict]` — 必须包含 `symptom_id`, `symptom_summary`, `evidence_refs`, `category`, `affects_next_gate`, `requires_next_slice`, `occurrence_count`
- `existing_issues: list[str]` — 已知 issue_id，用于 S2 去重
- `date: str` — 格式 `YYYY-MM-DD`

### 输出

```python
{
    "decisions": [
        {"symptom_id": "...", "verdict": "PROMOTE|SUPPRESS", "reason": "..."},
        ...
    ],
    "promoted_issues": [
        {"issue_id": "...", "title": "...", "category": "...", ...},
        ...
    ],
    "packet": {
        "packet_id": "fp-2026-04-16-001",
        "judgment": "...",
        ...
    } | None,  # None if no PROMOTE
    "consumer_payloads": {
        "direction-candidates": {...},
        "checklist": {...},
        ...
    } | None
}
```

### 不做清单

- 不修改 `Pipeline.process()`
- 不修改 checkpoint / handoff / CURRENT.md
- 不持久化 ConsumerPayload 到目标文档
- 不实现 evidence 自动提取（symptoms 由调用者提供）
- 不修改现有 MCP 工具签名

### 实现文件变更预估

| 文件 | 变更 |
|------|------|
| `src/dogfood/__init__.py` | 新增 `run_full_pipeline()` 协调函数 |
| `src/mcp/tools.py` | 新增 `promote_dogfood_evidence()` 方法 |
| `src/mcp/server.py` | 注册新工具到 `list_tools` 和 `call_tool` |
| `tests/test_dogfood_mcp.py`（新建） | MCP 工具集成测试 |

### 验证门

- [ ] `promote_dogfood_evidence` MCP 工具可被调用
- [ ] 传入 ≥2 个 symptoms（其中 1 个命中 T1），返回正确的 PROMOTE/SUPPRESS 分布
- [ ] 传入 0 个 PROMOTE 时，packet 和 payloads 为 None
- [ ] 全量回归 ≥ 964 passed

## 权威引用

- [design_docs/dogfood-evidence-issue-feedback-boundary.md](../design_docs/dogfood-evidence-issue-feedback-boundary.md) — 三层分工规范
- [design_docs/dogfood-promotion-packet-interface-draft.md](../design_docs/dogfood-promotion-packet-interface-draft.md) — 函数签名
- [src/dogfood/](../src/dogfood/) — 已实现管道
- [src/mcp/tools.py](../src/mcp/tools.py) — MCP 工具现有注册模式
- [review/claude-managed-agents-platform.md](../review/claude-managed-agents-platform.md) — B-REF-7 custom tool surface 合并审计（相关但不阻塞）
