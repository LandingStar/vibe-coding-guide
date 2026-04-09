# Effect Runtime Hook Profile Usage Guide

## 1. 文档定位

本文件面向**引擎使用者**，说明当前 effect runtime hook profile 的最小使用方式。

它关注的是：

- effect 在运行时如何挂接监听行为
- 而不是 effect 如何声明 modifier

---

## 2. 适用范围与何时使用

当前推荐使用这套入口来表达：

- effect 在哪个事件点挂接 runtime 行为
- effect 的衰减 / tick / 移除如何复用已有 profile
- runtime 中哪些监听行为已不再需要直接按 `effect_type` 硬编码分支

它当前尤其适用于：

- turn-end decay 类效果
- turn-end tick + decay 类效果

---

## 3. 入口位置

当前 runtime hook profile 入口位于：

- `standard_components/effects/authoring.py`
- `standard_components/effects/controller.py`

effect definition 通过：

- `runtime_hook_profile_key`

声明自己要绑定哪类运行时 hook。

---

## 4. 核心概念与声明结构

在 `Phase 15` 之前，effect 的 runtime listener 行为仍然主要按 `effect_type` 写在 controller 内部。

当前引入 runtime hook profile，是为了把：

- 这个 effect 在什么事件点挂监听
- 触发时做什么
- 怎样衰减 / 结束

从纯粹的 `effect_type` 分支里，推进到一个最小但明确的 profile 入口。

当前内建了两个 profile：

### `TURN_END_DECAY`

用途：

- 在 owner 的 `TURN_END` 递减 `remaining_turns`
- 到期后移除 effect

适用：

- `ATTACK_UP`
- `HASTE`

### `TURN_END_TICK_DAMAGE_AND_DECAY`

用途：

- 在 owner 的 `TURN_END` 先发布 tick/damage
- 然后递减 `remaining_turns`
- 到期后移除 effect

适用：

- `POISON`

---

## 5. 最小使用方式

定义时只需要把 profile key 写进 `EffectDefinition`：

```python
EffectDefinition(
    effect_type="POISON",
    description="Deal damage on the owner's TURN_END for a limited number of turns.",
    required_metadata_keys=("damage_per_tick",),
    optional_metadata_keys=("applier_id",),
    runtime_hook_profile_key="TURN_END_TICK_DAMAGE_AND_DECAY",
    tags=("listener", "turn_decay", "damage_over_time"),
)
```

当前 runtime 会根据 profile key 选择已支持的 hook 行为。

---

## 6. 发现与观察路径

CLI 中可直接输入：

```text
effects
```

它会同时列出：

- 当前已注册的 effect definitions
- 当前已注册的 runtime hook profiles

如果要看命令帮助：

```text
help effects
```

---

## 7. 当前边界

这套 profile 机制当前只保证：

- 最小 runtime hook 选择入口
- 内建 profile 的注册与列出
- 与现有快照、predictive、recover 路径兼容

当前还**不**保证：

- 任意自定义 hook 的完整脚本化
- listener phase 的外部 profile 化
- 更复杂的 runtime hook 组合

也就是说，当前它是一个 **seed**，不是完整的 effect runtime scripting 系统。

---

## 8. 相关文档

- `Authoring Documentation Standard.md`
- `Effect Authoring Surface Usage Guide.md`
- `design docs/stages/authoring-surface/Phase 16 Effect Runtime Hook Profile Slice.md`
