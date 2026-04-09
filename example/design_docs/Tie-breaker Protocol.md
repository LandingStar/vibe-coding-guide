# 📄 补充文档 1-B：同位撞线的确定性排序级联协议

**(Deterministic Cascade Sorting Protocol for Tie-breakers)**

## 1. 核心设计目的

在 C/S 状态同步架构中，双端计算的**绝对确定性（Determinism）**是底线。当发生时间跳跃（Tick）或大拉条事件，导致多个实体的行动值同时满足 $AV \le 0$ 时，严禁使用依赖运行环境稳定性的默认排序或随机数。

## 2. 排序元组级联规则 (Cascade Sorting Tuple)

时间轴组件在筛选出所有待行动实体后，必须生成一个严格的排序元组（Tuple）进行降序比较。每一级条件仅在前一级完全相等时才进行判定：

- **第一级：超量距离 (Over-distance, $D_{over}$)**
    
    冲出终点线最远的实体拥有绝对优先权。
    
    **公式：** $D_{over} = |AV| \times V_{current}$
    
- **第二级：基础速度 (Base Speed)**
    
    若超量距离一致，则比较实体的不含任何 Buff 修饰的初始面板速度。天生高速度的实体获得优先权。
    
- **第三级（可选机制）：阵营权重 (Optional Faction Weight)**
    
    引擎组件提供 `enable_faction_tiebreaker` 配置项。若引擎使用者开启此项，则根据预设权重判定（如：玩家阵营权重 > 敌对阵营权重）。若未开启，则直接跳过此级比较。
    
- **第四级（终极保底）：实体全局 ID (Global Entity ID)**
    
    若上述所有条件均完全相同（如同阵营的两个同质怪物），最终比对在游戏初始化时引擎为其分配的、全局唯一且自增的 `Entity_ID`。利用整数的绝对大小完成最终僵局的打破（Tie-breaker）。
    

---
