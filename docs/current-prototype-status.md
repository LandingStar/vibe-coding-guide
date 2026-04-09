# Current Prototype Status

## 文档定位

本文件用于封存当前已经做出的原型资产状态，防止它们在平台文档定型前被误当成正式权威方案。

## 当前结论

当前仓库里的原型资产主要是：

- `doc-loop-vibe-coding/`

它们现在的状态应视为：

- `prototype`
- `frozen for documentation-first review`

也就是：

- 保留现状
- 不立即扩写为正式平台实现
- 先以新平台文档为准重新审视

## 原型的用途

这些原型当前可以用于：

- 帮助讨论实例应该长什么样
- 暴露平台需要哪些抽象层
- 为后续复审提供具体材料

## 原型的限制

在文档优先阶段，原型不应用来：

- 直接定义平台边界
- 反向决定核心模型
- 充当最终插件规范
- 充当最终分发形态

## 复审时应问的问题

后续回看这些原型时，至少应逐项检查：

- 它实现的是平台能力，还是实例能力
- 它写死了哪些本应可扩展的假设
- 它隐含了哪些未正式写入平台文档的规则
- 它是否错误地把“文档实例”写成了“平台本体”

当前建议复审时至少对照以下权威文档：

- `docs/core-model.md`
- `docs/plugin-model.md`
- `docs/pack-manifest.md`
- `docs/governance-flow.md`
- `docs/review-state-machine.md`
- `docs/subagent-management.md`
- `docs/subagent-schemas.md`
- `docs/official-instance-doc-loop.md`
- `docs/project-adoption.md`

## 当前权威来源

在当前阶段，权威来源应按以下顺序理解：

1. 根目录 `docs/` 下的平台文档
2. 用户后续明确提出的新约束
3. 被封存的原型资产

`example/` 依然只是参考语料，不是平台协议本身。
