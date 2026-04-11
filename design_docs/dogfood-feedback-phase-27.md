# Dogfood 反馈 — Phase 27

> 日期: 2026-04-10
> 基线: 555 passed, 2 skipped (Phase 26)
> 执行方式: CLI `python -m src process/check` + Python 直接调用 GovernanceTools

## 场景执行结果

### 场景 1: governance_decide 处理 issue-report

**输入 A（中文）**:
> checkpoint.py的todos参数不支持字符串列表，write_checkpoint要求传dict但函数签名没有说明清楚，用户容易传错格式导致AttributeError

**结果**: intent=ambiguous, confidence=low → escalation 触发

**输入 B（英文）**:
> Bug report: write_checkpoint raises AttributeError when todos parameter receives a list of strings instead of list of dicts

**结果**: intent=correction, confidence=high → delegation → fallback to review

#### 发现

| ID | 问题 | 严重程度 | 详情 | 修复建议 |
|---|------|----------|------|----------|
| F1 | 中文 issue-report 分类为 ambiguous | 中 | keyword_map 中 issue-report 只有 ["issue", "problem", "report", "问题", "报告"]，缺少 "bug", "错误", "异常", "崩溃", "error" 等常见 bug report 词汇 | 扩充 keyword_map |
| F2 | 英文 bug report 分类为 correction 而非 issue-report | 低 | "report" 在 issue-report 关键词中，但 keyword matching 逻辑中 correction 的 "fix" 相关词可能先匹配 | 让 "bug" 成为 issue-report 关键词 |
| F3 | delegation fallback to review | 信息 | dry-run 模式下无 worker/contract_factory → 预期行为 | 无需修复 |
| F4 | registered_validators 为空 | 低 | validate_doc_loop/validate_instance_pack 被 skipped | 可能因路径解析问题，PackRegistrar 加载相对路径时 base_dir 不匹配 |

### 场景 2: check_constraints 状态恢复

**输入**: `python -m src check "测试check_constraints功能"`

#### 发现

| ID | 问题 | 严重程度 | 详情 | 修复建议 |
|---|------|----------|------|----------|
| F5 | current_phase 显示 Phase 26 | 中 | Checklist 的 Phase 21 write-back 已更新但 checkpoint 仍指向旧数据。constraint checker 从 Checklist 解析 phase | 需要在 Phase write-back 同时更新 checkpoint |
| F6 | active_planning_gate 未检测到 Phase 27 | 中 | Phase 27 planning gate 已 APPROVED 但 constraint checker 只扫描 "pending"/"candidate"，不扫描 "APPROVED" | 扩展扫描关键词包含 "APPROVED" |
| F7 | files_to_reread 不含 checkpoint | 低 | `.codex/checkpoints/latest.md` 不在恢复文件列表中 | 将 checkpoint 加入 files_to_reread |
| F8 | `check` 命令输出过多 | 低 | 同时输出 constraint 结果和完整 governance chain，对纯约束检查场景信息过多 | 分离 `check` 和 `process` 输出 |

### 场景 3: writeback_notify phase 推进

**输入**: `GovernanceTools.writeback_notify('Phase 27: Dogfood Verification')`

#### 发现

| ID | 问题 | 严重程度 | 详情 | 修复建议 |
|---|------|----------|------|----------|
| F9 | 10 个已关闭 gate 误报为 pending | **高** | 文件前 500 字符 scan 用 `"pending" in head.lower() or "candidate" in head.lower()` 匹配，已关闭的 gate 中的 "candidate" 或 "pending" 出现在标题/正文中导致误报 | 改为解析 Status 行（如 `Status: **CLOSED**` vs `Status: **APPROVED**`），只返回 status != CLOSED 的 |
| F10 | README.md 被当成 pending gate | **高** | planning-gate 目录下的 README.md 不是 gate 文档 | 过滤掉 README.md |
| F11 | 部分旧 gate 无 CLOSED 标记 | 低 | 部分历史 planning gate 可能没有统一的 Status 行 | 统一 gate 文档格式，或放宽解析 |

## 总结

### 本 Phase 内已修复

1. **F9 + F10**: `writeback_notify()` 已改为按 Status 行解析 pending gate，并过滤 `README.md`
2. **F6**: `check_constraints()` 已支持在 checkpoint 未声明 active gate 时回退扫描 `APPROVED/DRAFT` planning gate
3. **F7**: `check_constraints()` 已将 `.codex/checkpoints/latest.md` 加入 `files_to_reread`
4. **F1**: 已在 Phase 28 修复——`issue-report` 关键词扩充 + `correction/issue-report` tie-break
5. **F5**: 已在 Phase 28 修复——`writeback_notify()` live 路径会同步刷新 checkpoint phase
6. **F8**: 已在 Phase 30 修复——CLI `check` 改为默认只输出约束 / 状态信息；若提供文本输入，会明确引导用户改用 `process`
7. **F4**: 已在 Phase 31 修复——PackRegistrar 新增 `skipped_details` 诊断信息，官方实例当前脚本的 skipped 原因已明确为 `missing-validate`，而不是路径解析黑箱

### 中优先级（记录为 backlog）

8. **validator 语义升级（可选）**: 当前只澄清 skipped 原因，不自动把独立脚本升级为可执行 validator

### 低优先级（记录为 backlog）

9. **F2**: issue-report vs correction 的优先级仲裁
10. **F11**: 旧 gate 文档格式统一
