# M7 Transport Resilience and Timeline Entry Scope

## 1. 文档定位

本文件描述 `M6` 收口后的下一阶段主线。

`M7` 不再以“是否能建立 socket 通信”为目标；这个目标已经在 `M6` 达成。下一阶段的重点是把 transport 做稳，并准备 Timeline driver 进入主线。

当前建议按更窄的子切片推进：

- `M7-A`：Transport Resilience and Sync Diagnostics
- `M7-B`：Timeline authoritative 首切片
- `M7-C`：Timeline predictive / replay / resync

范围约束以 `Post-MVP Scope Guardrails and Next-Step Plan.md` 为准。

---

## 2. 主要内容

### 2.1 传输韧性

- 更明确的 connect / attach / shutdown 契约
- 断链、超时与失败语义
- transport 层错误如何向 CLI / 宿主抬升
- 协议版本与兼容性边界

### 2.2 同步与调试工具增强

- 更系统的 desync 场景注入
- 更清晰的 sync/recovery 输出
- 更丰富的宿主侧状态检查接口
- transport 诊断 CLI，如 `transport` / `ping`

### 2.3 Timeline driver 进入主线

- 在 authoritative 模式下先接入 Timeline
- 再把 predictive / replay / resync 迁移到 Timeline
- 固定 timeline 下的 token / binding / window 投影语义

---

## 3. 当前不建议优先做的事

- 继续堆更多 demo 技能
- 在 transport 韧性不足时直接扩多客户端房间
- 在 Timeline 未进入 authoritative 主线前就推进复杂网络化连锁
- 在同一轮里同时重构 transport、快照和 driver 主线

---

## 4. 与 MVP 的关系

`MVP` 已经完成，当前没有剩余阻塞项。

`M7` 及之后的工作属于 post-MVP 增强，而不是补 MVP 漏洞。
