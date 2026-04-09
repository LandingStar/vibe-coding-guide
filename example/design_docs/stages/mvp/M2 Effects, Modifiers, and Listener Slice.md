# 📄 实现规划文档：M2 效果、修饰器与监听器首切片

**(Implementation Plan: M2 Effects, Modifiers & Listener Slice)**

## 1. 文档定位

本文件用于记录项目在 `M1` 之后进入的下一个实现阶段：

- **`M2`**

当前 `M2` 不等于“完整 Buff 标准库已完成”，而是：

- 先落一条最小可运行的效果链
- 让属性求值、效果挂载、回合衰减、监听器触发第一次在代码中真正串起来

---

## 2. 当前 `M2` 范围

当前 `M2` 首切片明确包含：

- `standard_components/attributes/service.py`
  - 最小 `AttributeService`
  - 最小 `ModifierRecord`
  - 默认 bucket/evaluator

- `standard_components/effects/controller.py`
  - 最小 `EffectRecord`
  - 基于 `World.global_payload` 的效果存储
  - 基于 `TURN_END` 的回合衰减监听
  - 效果监听器的导入后重建
  - `authoritative / projection` 执行画像下的不同派生事件策略
  - 对 stale `TURN_END` 的 projection 防护

- `demo/basic_combat.py`
  - `BasicAttack` 改为默认读取攻击属性
  - 新增 `RALLY` 命令
  - 新增 `POISON` 命令
  - 新增 `APPLY_EFFECT` 事件

- `demo/session.py` / `demo/cli.py`
  - 控制台中可直接使用 `rally`
  - 控制台中可直接使用 `poison [target_id]`
  - `status` 会展示当前 ATK 与激活效果
  - 控制台会明确打印 `poison` tick 伤害，避免回合观感混淆

- 快照恢复与测试注入
  - `ServerHost.export_snapshot()`
  - `ClientHost.recover_from_snapshot()`
  - `LocalBattleSession.recover_client_from_server_snapshot()`
  - `tests/support/scenario_tools.py`

---

## 3. 当前已实现的最小效果链

当前首条效果链如下：

1. 玩家在自己回合使用 `RALLY`
2. 服务端派发 `APPLY_EFFECT`
3. `EffectController` 为当前 actor 挂载 `ATTACK_UP`
4. `AttributeService` 在后续 `BasicAttack` 读取攻击值时纳入该修饰器
5. 效果在拥有者的 `TURN_END` 上衰减
6. 到期后自动移除

当前 CLI 中已经可以观察到：

- `ATK` 数值变化
- `Effects[ATTACK_UP(1)]` 这类状态显示

当前第二条监听器效果链如下：

1. 玩家在自己回合使用 `POISON`
2. 服务端派发 `APPLY_EFFECT`
3. `EffectController` 为目标挂载 `POISON`
4. 目标在自己的 `TURN_END` 上触发持续伤害
5. 效果在每次 tick 后衰减，到期后自动移除

当前 CLI 中已经可以观察到：

- `Effects[POISON(2)] / Effects[POISON(1)]`
- 目标 HP 在自己回合结束后被持续伤害压低
- `Slime suffers 3 poison damage.` 这类回合结束提示

---

## 4. 当前明确不做的内容

当前 `M2` 首切片仍不包含：

- 完整 Buff 类型注册表
- 完整 Listener lane/band/profile 落地
- 多种叠层策略的全面业务覆盖
- 多种效果锚点（如 `RoundEnd`、`WindowStart`）
- 完整快照协议下的效果重建与增量同步
- Timeline driver 下的效果协同

换句话说，当前只是：

- **最小效果链成立**

而不是：

- **Buff 标准库整体完工**

---

## 5. 当前阶段判断

当前项目状态更准确地说是：

- `M1` 已通过手动控制台验收
- `M2` 的首个修饰器/监听器切片已经可运行并基本收口
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `75 passed`

下一步最合理的方向是：

1. 继续打磨当前 `ATTACK_UP / RALLY / POISON` 这三条最小链路
2. 再决定是否继续接第二种监听器锚点或更通用的效果同步事件
3. 然后再考虑更完整的 Buff / Listener 标准库边界
