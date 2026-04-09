# OpenHands Research

## 产品定位

OpenHands 是面向 coding agent 的开放平台。对我们最重要的不是它的“会写代码”，而是它对：

- always-on context
- on-demand skills
- 项目 / 用户 / 组织 / 全局技能分层

这些机制的处理。

## 关键机制

- `AGENTS.md` 用于 repository-wide 的永久上下文。
- 技能分成 always-on context 与 on-demand skills 两类。
- on-demand skills 支持 progressive disclosure：先看摘要，再按需加载完整内容。
- 官方 global skill registry 维护在 `github.com/OpenHands/extensions`。
- skills 有明确 precedence：
  - `.agents/skills/`
  - `.openhands/skills/`（deprecated）
  - `.openhands/microagents/`（deprecated）
- 项目级 skills 优先于用户级 skills。
- 还支持组织级与用户级共享 skills。

## 对我们最有价值的点

- 明确区分“始终在上下文中”的规则与“按需展开”的技能。
- 让项目级、用户级、组织级、全局 registry 共存。
- 把 skill 当成一个带资源目录的包，而不是单独 prompt 文件。

## 与我们目标的差异

- OpenHands 更偏 coding agent 平台与上下文扩展，不是规则治理引擎。
- 它的强项在技能加载，不在 policy decision / gate execution。
- 子 agent 管理不是技能系统的重点，更多是能力注入与上下文塑形。

## 对子 agent 管理的启发

间接启发很强：

- 主 agent 与子 agent 需要不同层级的上下文装载策略。
- 项目常驻规则不应该和可选技能混在一起。
- 子 agent 消费的材料应尽量 progressive disclosure，而不是全量灌入。

## 我们可吸收的设计点

- `always-on context` / `on-demand pack content` 二分法
- 项目 / 用户 / 组织 / 全局四层 pack 来源
- pack 目录化与资源化
- skill registry 思路

## 当前不应直接照搬的点

- 不应把 skill 系统本身当成平台核心
- 不应把“上下文注入”误当成完整的治理流程

## 主要来源

- https://docs.openhands.dev/overview/skills
- https://docs.openhands.dev/overview/skills/org
- https://github.com/OpenHands/OpenHands
- https://github.com/OpenHands/extensions
