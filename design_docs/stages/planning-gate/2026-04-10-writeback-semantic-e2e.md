# Planning Gate — Write-Back 语义文档更新 + E2E 治理测试与 Reviewer 入口

- Status: **CLOSED**
- Phase: 14
- Date: 2026-04-10

## 问题陈述

Phase 12 实现了 WritebackEngine，但 `plan()` 仅生成通用摘要文件（`.codex/writebacks/{id}.md`），无法操作真实文档（如更新 Checklist 中某行状态、在 Phase Map 中追加条目）。`docs/governance-flow.md` Step 7 要求"write back artifact"，当前实现名存实亡。

同时，ReviewOrchestrator（Phase 13）逻辑完整但仅能通过 Python 内部调用，无外部入口供 reviewer（人或 agent）提交 feedback。E2E 测试覆盖也缺乏完整的治理流程路径。

## 切片计划

### Slice A — Write-Back 语义文档更新

**范围：**
- 定义 write-back directive schema（JSON）：
  - `target_path`：目标文件
  - `operation`：`section_replace` / `section_append` / `line_insert` / `line_replace` / `full_rewrite`
  - `match`：定位策略（`heading` / `line_pattern` / `line_number` / `anchor_marker`）
  - `content`：新内容
  - `content_type`：markdown / json / yaml / text
- 创建 `src/pep/markdown_updater.py`：
  - `find_section(lines, heading)` → 返回 section 起止行号
  - `replace_section(lines, heading, new_content)` → 替换整个 section
  - `append_to_section(lines, heading, content)` → 在 section 尾部追加
  - `insert_after_line(lines, pattern, content)` → 在匹配行后插入
  - `replace_line(lines, pattern, new_line)` → 替换匹配行
- 更新 `WritebackEngine.plan()` 支持 directive-based plan 生成
- 更新 `WritebackEngine.execute_plan()` 支持 directive 操作

**不做：**
- 不实现 JSON/YAML AST 级别操作（留给后续）
- 不实现 Jinja2 模板引擎
- 不处理并发写入冲突

### Slice B — E2E 治理测试 + Reviewer 外部入口

**范围：**
- 创建 `tests/test_governance_e2e.py`：覆盖完整治理路径
  - question → inform → applied（快速路径）
  - correction → review → waiting_review → approve → applied → writeback
  - scope-change → approve → escalation → reject → terminal
  - correction → review → request_revision → revision → resubmit → approve → applied
  - delegation → contract → worker → report → auto-apply
- 创建 `src/review/feedback_api.py`：
  - `FeedbackAPI(executor)` 类
  - `submit(envelope_id, feedback, reason)` → 查找已执行结果 → 调用 executor.apply_review_feedback()
  - 基于 dict 的 in-memory result 存储
- 测试 `tests/test_feedback_api.py`

**不做：**
- 不实现 REST / HTTP server（留给后续）
- 不实现持久化存储（in-memory 即可）

## 验证门

1. `pytest tests/` 全部通过（无回归）
2. Markdown section 更新测试覆盖：find / replace / append / insert / replace_line
3. E2E 测试覆盖至少 4 条完整治理路径
4. FeedbackAPI 可从外部提交 approve/reject/revision

## 边界

- Slice A 仅处理 Markdown 文档更新
- Slice B 外部入口为 Python API，不含 REST/CLI
- 不扩展 intent classifier 或 gate resolver 的规则配置化
