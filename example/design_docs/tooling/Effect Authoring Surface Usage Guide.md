# Effect Authoring Surface Usage Guide

## 1. 文档定位

本文件面向**引擎使用者**，说明当前最小 effect authoring surface 的使用方式。

它不是阶段范围文档，因此放在 `design docs/tooling/`，而不是 `design docs/stages/`。

---

## 2. 适用范围与何时使用

当前推荐使用这套入口来定义：

- 只包含 modifier 的效果
- 需要基本 metadata 的效果
- 需要在 runtime 中被 catalog / registry 统一识别的效果

当前内建样例包括：

- `ATTACK_UP`
- `HASTE`
- `POISON`

---

## 3. 入口位置

当前最小作者化入口位于：

- `standard_components/effects/authoring.py`
- `standard_components/effects/controller.py`

---

## 4. 核心概念与声明结构

核心概念有 3 个：

1. `EffectDefinition`
2. `ModifierTemplate`
3. `EffectRegistry`

一个 effect definition 需要回答：

- `effect_type`
- `description`
- `modifier_templates`
- `required_metadata_keys`
- `runtime_hook_profile_key`

---

## 5. 最小使用方式

定义一个最小 effect 时，通常先写 `EffectDefinition`：

```python
EffectDefinition(
    effect_type="ATTACK_UP",
    description="Add a flat attack modifier for a limited number of turns.",
    modifier_templates=(
        ModifierTemplate(
            attribute_key="attack",
            bucket_key="FLAT_ADD",
            metadata_key="flat_attack",
            stack_key_template="{owner_id}:ATTACK_UP",
            stack_policy_key="HIGHEST_ONLY",
        ),
    ),
    required_metadata_keys=("flat_attack",),
    runtime_hook_profile_key="TURN_END_DECAY",
    tags=("modifier", "turn_decay"),
)
```

当前推荐通过 `EffectController.build_effect(...)` 构建 effect，而不是手写 `EffectRecord`：

```python
effect = runtime.effect_controller.build_effect(
    effect_type="ATTACK_UP",
    owner_id="hero",
    remaining_turns=2,
    metadata={"flat_attack": 5},
)
runtime.effect_controller.apply_effect(effect)
```

`APPLY_EFFECT` 当前也已经走这条通用入口。

---

## 6. 发现与观察路径

CLI 中可直接输入：

```text
effects
```

它会显示：

- 当前已注册的 effect definitions
- 当前已注册的 runtime hook profiles

如果要看命令帮助：

```text
help effects
```

---

## 7. 当前边界

这套入口当前只保证：

- definition / registry / build
- 最小 metadata 校验
- 与现有 runtime、快照、predictive、recover 兼容

当前还**不**保证：

- 外部文件配置化
- 脚本化 effect
- 完整 runtime hook 作者化
- 第二个内容切片

---

## 8. 相关文档

- `Authoring Documentation Standard.md`
- `Effect Runtime Hook Profile Usage Guide.md`
- `design docs/stages/authoring-surface/Phase 15 Effect Authoring Surface Seed.md`
