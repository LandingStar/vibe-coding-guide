# Phase 15 Effect Authoring Surface Seed

## 1. 阶段定位

本阶段不新增新的调度语义，也不重写现有效果运行时。

它的目标是把当前已经落地的：

- `effect`
- `modifier`
- `listener`

整理成一个**最小但明确**的 authoring surface，让已有能力不再只能靠 demo 内部硬编码逐项拼装。

---

## 2. 本阶段只回答的问题

在保持现有效果运行时语义不变的前提下：

**如何为当前 effect 机制提供一个可注册、可描述、可复用的最小声明面。**

---

## 3. 实现边界

本阶段只做：

1. 为 effect 定义最小声明结构
   - `EffectDefinition`
   - `ModifierTemplate`
   - `EffectRegistry`
2. 在 `EffectController` 上提供：
   - 注册入口
   - 列表入口
   - 通用 build/apply 入口
3. 将当前内建 effect 迁移到这套声明面
   - `ATTACK_UP`
   - `HASTE`
   - `POISON`
4. 提供一个最小开发者观察面
   - CLI `effects`
5. 保持现有 runtime、projection、predictive、recover、验证平台入口可直接复用

本阶段明确不做：

1. 第二个 demo slice
2. effect 脚本系统
3. effect 的外部文件配置化
4. listener phase profile 重写
5. 新的 timeline 调度语义
6. rollback / snapshot 契约改写

---

## 4. 当前产物

当前阶段已落地：

- `standard_components/effects/models.py`
- `standard_components/effects/authoring.py`
- `EffectController.registry`
- `EffectController.build_effect(...)`
- `demo/cli.py` 的 `effects`
- `tests/components/test_effect_authoring.py`
- `tests/acceptance/test_phase15_acceptance.py`

`APPLY_EFFECT` 当前已经改为通过通用 authoring surface 构建 effect，而不是继续在 executor 内对每种 effect 写一段独立构造逻辑。

---

## 5. 当前验收标准

本阶段通过的标准是：

1. runtime 默认安装 effect registry
2. 当前内建 effect 定义可被列出与描述
3. `APPLY_EFFECT` 通过通用 authoring surface 构建 effect
4. CLI `effects` 能直接显示当前 effect catalog
5. 现有 `RALLY / HASTE / POISON` 运行路径不回归

---

## 6. 为什么本阶段该停在这里

本阶段的重点是：

- 把 effect 从“只能内部硬编码构造”推进到“已有最小声明面”
- 给未来作者化继续深化留出明确入口

如果继续往下做，就会进入另一类问题：

- listener runtime hook 的声明化
- 更通用的 effect profile
- 外部配置面
- 第二个内容切片

这些都不再属于同一个“authoring surface seed”切片。

---

## 7. 对后续阶段的意义

若本阶段完成，则项目应具备：

- 一个可长期演化的 effect 声明入口
- 一个可直接检查当前 effect catalog 的开发者界面
- 一个不依赖 demo 内部 if/elif 扩张的最小作者化基线
