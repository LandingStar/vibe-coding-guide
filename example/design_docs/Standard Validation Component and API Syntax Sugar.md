# 📄 子文档 3-A-2：校验器 API 设计与开发者指南

**(Implementation: Validator API & Developer Experience)**

## 1. 接口规范：极致包容的签名设计

校验器基类放弃了固定参数，统一使用 `(event, world)` 签名，实现接口的绝对泛化。

Python

```
class BaseValidator:
    def validate(self, event: BaseEvent, world: GameWorld) -> bool:
        """
        所有具体校验器必须实现此接口。
        按需从 event 提取上下文，与 world 状态进行比对。
        """
        raise NotImplementedError
```

## 2. 标签系统 (Tag System) 的高性能实现

底层摒弃硬编码状态。实体的所有瞬时状态抽象为 `Tag`，并在引擎初始化时映射为全局唯一的**二进制位掩码 (Bitmask)**。这使得校验器在比对 `world` 中的实体状态时，只需进行 $O(1)$ 复杂度的高效位运算。

## 3. 开发者体验 (DX)：隐藏组合器的语法糖

底层采用**组合模式 (Composite Pattern)** 构建复合校验逻辑。通过重写 Python 的魔术方法（`__and__`, `__or__`, `__invert__`），对业务开发者彻底隐藏 AST（抽象语法树）的嵌套复杂度。

Python

```
# --- 业务开发者编写的静态技能配置脚本 ---

# 1. 实例化基础校验单元 (底层隐式接收 event 和 world 进行解析)
# 例如，RequireTargetTag 内部会自动去查 world.get_entity(event.target_ids)
is_target_alive = RequireTargetTag("ALIVE")
is_target_enemy = RequireTargetTag("ENEMY")
not_invincible = ~RequireTargetTag("INVINCIBLE") 
in_range = CheckDistance(max_dist=2.0) # 内部自动比对 event.source 和 event.target 的坐标

# 2. 极其符合人类直觉的逻辑拼装 (底层自动构建 AndValidator 等组合器)
fireball_validation = is_target_alive & is_target_enemy & not_invincible & in_range

# 3. 静态注册
SkillRegistry.register(
    skill_id="Fireball",
    validator=fireball_validation,
    fallback=Strategy.FIZZLE
)
```

---
