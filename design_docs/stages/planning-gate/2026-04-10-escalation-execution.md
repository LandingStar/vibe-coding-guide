# Planning Gate — 升级路径执行

- Status: **CLOSED**
- Phase: 10
- Date: 2026-04-10

## 问题陈述

当 PDP escalation_decision 指示 `escalate=true` 时，PEP 当前只做 log/queue，没有执行升级路径的实际逻辑。需要：
- `target=human_reviewer`：生成通知并暂停执行，等待人类审核
- `target=main_agent`：将决策回传给主 agent 重新评估

## 解法

沿用依赖反转模式：定义 `EscalationNotifier` Protocol，PEP 通过接口调用。

```
Slice A: 升级通知纯函数 + Protocol
         ├── EscalationNotifier protocol (src/interfaces.py)
         ├── notification_builder.py — 生成通知对象
         └── stub_notifier.py — 最小可测实现

Slice B: PEP 集成
         ├── executor.py — 识别 escalation_decision 并路由
         ├── 端到端测试
         └── write-back
```

## 切片计划

### Slice A — 通知构建 + Stub

**范围：**
- 在 `src/interfaces.py` 添加 `EscalationNotifier` Protocol
- 创建 `src/pep/notification_builder.py`
  - `build(envelope, escalation_decision) -> dict` 生成通知对象
  - 包含 target、reason、context、建议动作
- 创建 `src/pep/stub_notifier.py`
  - 实现 EscalationNotifier，记录通知到内存列表
- 测试

### Slice B — PEP 集成

**范围：**
- 更新 `src/pep/executor.py`：
  - 当 envelope 有 `escalation_decision.escalate=true` 时，在委派/正常流程之后追加升级处理
  - `target=human_reviewer`：调用通知器 + 结果标记为 `escalated`
  - `target=main_agent`：记录 log + 结果标记为 `re-evaluate`
- 端到端测试
- write-back

## 验证门

- [x] `pytest tests/` 全部通过 — 93 passed, 1 skipped
- [x] notification_builder 输出结构正确
- [x] PEP 端到端测试包含升级场景
- [x] `validate_doc_loop.py --target .` 通过

## 依赖

- `src/pdp/escalation_resolver.py`
- `src/pep/executor.py`（Phase 9 产出）

## 风险

- 升级通知在当前阶段无真正外部通道（email/webhook），仅为接口 + 内存记录。
