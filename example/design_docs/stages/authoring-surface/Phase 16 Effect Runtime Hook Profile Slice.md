# Phase 16 Effect Runtime Hook Profile Slice

## 1. 阶段定位

本阶段不新增新的调度语义，也不重写 effect runtime 的核心执行模型。

它的目标是把当前已经存在的 effect runtime listener 行为，推进成一个**最小但明确**的 runtime hook profile 入口。

---

## 2. 本阶段只回答的问题

在保持现有 effect runtime 语义不变的前提下：

**如何让 effect 的运行时 hook 不再直接按 `effect_type` 写死，而是通过最小 profile 入口进行选择。**

---

## 3. 实现边界

本阶段只做：

1. 为 effect runtime hook 定义最小 profile 概念
   - `RuntimeHookProfile`
   - `runtime_hook_profile_key`
2. 为 registry 增加 runtime hook profile 的注册与查询能力
3. 先迁移当前内建的两类 hook：
   - `TURN_END_DECAY`
   - `TURN_END_TICK_DAMAGE_AND_DECAY`
4. 用它们覆盖：
   - `ATTACK_UP`
   - `HASTE`
   - `POISON`
5. 在 CLI `effects` 中同时展示：
   - effect definitions
   - runtime hook profiles

本阶段明确不做：

1. 新的 effect 脚本系统
2. 第二个 demo slice
3. listener phase 的完整外部 profile 化
4. 新的 timeline 调度语义
5. 增量快照
6. rollback 改写

---

## 4. 当前产物

当前阶段已落地：

- `standard_components/effects/authoring.py` 中的 `RuntimeHookProfile`
- `EffectDefinition.runtime_hook_profile_key`
- `EffectRegistry` 的 runtime hook profile 注册能力
- `EffectController` 的 profile 选择式 runtime hook 安装
- `TURN_END_DECAY`
- `TURN_END_TICK_DAMAGE_AND_DECAY`
- `design docs/tooling/Effect Runtime Hook Profile Usage Guide.md`
- `tests/acceptance/test_phase16_acceptance.py`

---

## 5. 当前验收标准

本阶段通过的标准是：

1. runtime 默认暴露 runtime hook profile 列表
2. `POISON` 不再依赖 `effect_type == "POISON"` 这类 runtime 分支才能挂起 listener 行为
3. `ATTACK_UP / HASTE` 继续沿用最小 decay profile，不回归
4. CLI `effects` 能显示 runtime hook profiles
5. 对应使用文档已补到 `design docs/tooling/`

---

## 6. 为什么本阶段该停在这里

本阶段的重点是：

- 把 runtime hook 的选择入口抽出来
- 为后续 listener authoring 留出明确挂点

如果继续往下做，就会进入另一类问题：

- hook 组合
- listener phase 的更完整 profile 化
- 更外露的作者化文档标准
- 更强的内容配置面

这些都不再属于同一个“runtime hook profile”切片。

---

## 7. 对后续阶段的意义

若本阶段完成，则项目应具备：

- effect authoring 的 build 半边
- effect authoring 的 runtime hook 半边

这时作者化已经不再只是一层 catalog，而开始具备最小的运行时 profile 入口。
