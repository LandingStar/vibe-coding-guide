# Dogfood 反馈：MCP 工具真实使用场景测试（2026-04-21）

## 测试背景

在完成 Cline 外部项目研究后，使用平台 MCP 工具执行一轮真实治理工作流，包括：

- `check_constraints`：约束检查
- `get_pack_info`：Pack 状态查看
- `governance_decide`：两次治理决策（中文 + 英文输入）
- `query_decision_logs`：决策日志查询
- `analyze_changes`：变更影响分析
- `get_next_action`：下一步推荐
- `promote_dogfood_evidence`：dogfood 管道执行

## 收集的症状

### DF-2026-04-21-S1: Intent Classifier 覆盖率极低 — **已提升为 IC-001**

- 5 条 decision log 全部 `intent=unknown, confidence=low`
- 中文、英文、terminal-command 三类输入均未命中 `KEYWORD_MAP`
- 根因：`KEYWORD_MAP` 关键词集合过窄，无法覆盖真实使用场景

### DF-2026-04-21-S2: Gate 级别无差异化（S1 下游）

- 所有操作一律 `gate=review`（因 unknown → impact=medium → review）
- 管道判断：S1 的下游后果，S3 抑制

### DF-2026-04-21-S3: get_next_action 无 gate 时矛盾指令 — **已修复**

- 返回 `"Continue working on the active planning gate: 无活跃 gate"` 
- **根因**：checkpoint 文件中 `Active Planning Gate` 值为中文 `"无活跃 gate"`，不在 `_EMPTY_PLANNING_GATE_MARKERS` 集合中，导致 pipeline 将其视为有效 gate 名称
- **修复**：扩展 `_EMPTY_PLANNING_GATE_MARKERS`（`src/workflow/pipeline.py`），增加 `"无活跃 gate"`, `"无活跃gate"`, `"无"`, `"无活跃"`, `"none"`, `"n/a"` 六个标记
- **测试**：新增 6 个参数化测试用例（`tests/test_pipeline.py::test_check_constraints_chinese_empty_gate_markers`），全部通过
- **回归**：1284 passed, 2 skipped（+6 新测试，无回归）

### DF-2026-04-21-S4: analyze_changes 对非代码文件空结果

- `review/*.md` 不在依赖图中，返回空 impact + 空 coupling
- 判断：**符合设计预期**——依赖图聚焦 Python 源码

### DF-2026-04-21-S5: governance_decide 响应过于冗长

- 每次返回完整 `pack_info`（~100 行），包含 external_skill_interaction_contract 等重复数据
- 增加 LLM token 消耗
- 判断：可延后但值得优化

## Dogfood 管道结果

- 提升决策：S1 → IC-001（"Intent classifier 几乎总是返回 unknown"）
- 抑制决策：S2（S3 抑制）、S3（S1 抑制）、S4（S1+S3 抑制）、S5（S3 抑制）
- 反馈包 ID：`fp-2026-04-21-001`
- 置信度：high

## 元观察：Dogfood 管道本身表现

1. **Promotion 逻辑合理**：正确识别 S1 为根因，S2 为下游，其余为低优先级
2. **抑制逻辑保守**：S3（get_next_action 矛盾指令）被 S1 抑制不太合理——两者是独立问题，S3 修复工作量极小。建议 S1 出现次数阈值不应用于抑制独立的小缺陷
3. **Consumer payloads 结构完整**：direction-candidates / checklist / phase-map / checkpoint / handoff / planning-gate 六路分发均有输出
4. **缺少 affected_docs 精确填充**：`affected_docs` 为空字符串数组，这是因为 symptom 输入未包含 `evidence_refs.path` 以外的文档路径信息

## 行动项

| # | 项目 | 状态 | 优先级 |
|---|------|------|--------|
| 1 | S3 修复：get_next_action 无 gate 专用提示 | ✅ 已修复 | 即时 |
| 2 | S1/S2 根因：KEYWORD_MAP 扩展或替代分类器 | ✅ KEYWORD_MAP 大幅扩展 + implementation 意图新增 | 中 |
| 3 | S5 优化：governance_decide 响应瘦身 | ✅ pack_info 精简为摘要（name/version/kind + merged intents/gates），移除 external_skill_interaction_contract | 低 |
