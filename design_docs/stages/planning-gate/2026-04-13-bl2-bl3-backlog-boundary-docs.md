# Planning Gate — BL-2 / BL-3 Backlog Boundary Docs

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-13-bl2-bl3-backlog-boundary-docs |
| Scope | BL-2 adapter registry / BL-3 多协议转接层的边界、触发条件与文档落点收口 |
| Status | **DRAFT** |
| 来源 | `design_docs/direction-candidates-after-phase-35.md` §Driver / Adapter / 转接层 Backlog、`design_docs/Project Master Checklist.md`、`docs/plugin-model.md`、`docs/external-skill-interaction.md`、`review/research-compass.md` |
| 前置 | BL-1 Driver 职责定义文档已完成；当前无 active planning-gate |
| 测试基线 | 823 passed, 2 skipped |

## 问题陈述

当前 backlog 已把 BL-2 与 BL-3 分别记为：

- BL-2：Adapter 分类与统一注册框架
- BL-3：多协议转接层（远期）

但现有材料仍有两个边界风险：

1. 已存在的 `2026-04-13-bl2-adapter-registry.md` 直接跳到了实现型 registry 设计，容易越过“先文档化边界”的用户当前选择
2. BL-2 与 BL-3 在 `plugin-model` / `external-skill-interaction` / backlog 描述之间仍可能被误读为同一层能力

在进入任何实现 gate 之前，更稳妥的做法是先补一条纯文档切片，明确：

- BL-2 解决什么，不解决什么
- BL-3 何时才应该从储备项进入 planning-gate
- 二者与现有 driver / plugin / external skill contract 的关系

## 目标

**做**：
1. 为 BL-2 与 BL-3 明确能力边界、输入输出与触发信号
2. 说明它们与 `docs/plugin-model.md`、`docs/external-skill-interaction.md`、`docs/driver-responsibilities.md` 的衔接关系
3. 决定现有 `2026-04-13-bl2-adapter-registry.md` 是保留、 supersede 还是标注为后续实现 gate
4. 为下一轮用户选择提供更清晰的文档入口，而不是直接跳入代码实现

**不做**：
1. 不实现统一 adapter registry
2. 不新增多协议转接层代码或原型
3. 不修改 runtime / MCP / CLI 业务逻辑
4. 不把 backlog 记录扩成新的大范围架构 redesign

## 交付物

### 1. backlog 边界文档对齐

至少同步以下载体中的 BL-2 / BL-3 口径：

- `design_docs/direction-candidates-after-phase-35.md`
- `docs/plugin-model.md`
- `docs/external-skill-interaction.md`
- `design_docs/Project Master Checklist.md`（若需要记录当前裁决）

### 2. gate 生命周期裁决

明确记录：

- `2026-04-13-bl2-adapter-registry.md` 的后续状态
- BL-3 仍保持 backlog 还是进入更具体的分析文档

## 验证门

- [ ] BL-2 与 BL-3 的能力边界、触发条件、依赖关系在文档中一致
- [ ] `plugin-model` / `external-skill-interaction` / backlog surface 不再混淆 BL-2 与 BL-3
- [ ] 现有 `2026-04-13-bl2-adapter-registry.md` 的定位已明确（保留 / supersede / 延后）
- [ ] 本切片不引入业务代码改动；若实际触及代码，再补 targeted/full regression

## 收口判断

做到以下边界就应停：

1. 后续若要实现 BL-2，已具备清晰文档入口
2. BL-3 仍保持为远期能力，不会被误拉入当前版本范围
3. 用户下一次只需要在“继续 dogfood”与“进入 BL-2 实现 gate”之间做清晰选择