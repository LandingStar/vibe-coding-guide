# M8 Advanced Scheduling and Recovery Backlog

## 1. 文档定位

本文件记录 scoped post-MVP 完成后的候选下一阶段。

它不是当前已启动阶段，而是供后续决策使用的 backlog。

---

## 2. 下一阶段候选内容

如果继续推进，建议只从以下三类中选择一条主线启动：

### 2.1 Timeline 高级动力学

- 动态速度变化
- `SpeedChangedEvent` / `SchedulingMetricChangedEvent` 接入
- 拉条 / 推条
- `ScheduleAdjustEvent` / `WindowGrantEvent` 的 Timeline 主线解释

### 2.2 同步与恢复增强

- 增量快照
- 更细粒度 replay / rollback 契约
- reconnect 自动化
- 断链后的恢复策略

### 2.3 确定性与测试强化

- Timeline 数学模型测试
- 双 driver 一致性测试
- 更强的跨 transport 回归
- 更系统的 desync 场景矩阵

---

## 3. 当前明确不建议直接做的事

- 多客户端房间
- 账号/数据库/大厅
- 图形 UI 大改
- WebSocket / HTTP 平台化改造
- 继续大量扩 demo 技能

---

## 4. 当前建议

若继续推进，建议优先从：

`2.1 Timeline 高级动力学`

开始，但仍然保持单一窄切片，不要把动态速度变化、插队、reconnect 和增量快照捆在同一轮。
