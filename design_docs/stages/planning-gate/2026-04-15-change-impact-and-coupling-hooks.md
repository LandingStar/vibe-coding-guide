# Planning Gate — 变更影响分析与耦合钩子（Slice 2）

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-15-change-impact-and-coupling-hooks |
| Scope | 基于 Slice 1 图谱的变更影响传播 + 显式耦合标注 + 联动提醒 |
| Status | **DONE** |
| 来源 | `issues/issue_type_dependency_and_coupling_tracking.md` FR-2 |
| 前置 | Slice 1 `tools/dependency_graph/` 已完成（186 节点，56 边，850 passed） |
| 测试基线 | 872 passed, 2 skipped |

## 问题陈述

Slice 1 提供了可查询的依赖关系图谱，但缺少两个实用能力：

1. **变更影响分析**：修改了某个 Protocol 或类后，沿图谱自动枚举所有受影响的下游模块/符号
2. **耦合钩子**：有些联动关系不是类型依赖而是语义约束（如"改了 ErrorInfo 的字段必须同步改 docs/structured-error-format.md"），需要显式标注并在变更时触发提醒

当前 agent 在执行变更时只能手动搜索引用，容易遗漏间接依赖和语义耦合。

## 目标

**做**：

1. **变更影响传播器**（ImpactAnalyzer）
   - 输入：变更集（文件列表 or 符号列表）
   - 沿图谱 edges 向外传播（可配置传播深度）
   - 输出：按层级分组的受影响节点列表 + 影响路径
   
2. **耦合标注数据模型**（CouplingAnnotation）
   - 描述两个或多个位置之间的语义耦合关系
   - 结构化存储为 JSON 文件（`tools/dependency_graph/coupling_annotations.json`）
   - 支持 CRUD 维护
   
3. **联动提醒生成器**（CouplingChecker）
   - 给定变更集，匹配所有涉及的耦合标注
   - 输出联动提醒列表（哪些位置需要同步检查/更新）

4. **查询接口扩展**
   - `impact_of(changes)` — 返回影响分析结果
   - `coupling_check(changes)` — 返回耦合提醒

5. **Dogfood 验证**
   - 用实际场景验证：修改 `WorkerBackend` Protocol → 影响分析应列出 5 个依赖模块
   - 标注已知耦合对并验证触发

**不做**：

1. 不做自动修复（只做提醒/列出，不自动改代码）
2. 不做 MCP 工具集成（Slice 3）
3. 不做与 governance check_constraints 的集成（Slice 3）
4. 不做实时文件监控（基于显式调用）

## 数据模型

### 变更集（ChangeSet）

```python
@dataclass
class ChangeSet:
    """描述一组变更。"""
    changed_files: list[str] = field(default_factory=list)   # 变更的文件路径
    changed_symbols: list[str] = field(default_factory=list)  # 变更的符号 id
```

### 影响分析结果（ImpactResult）

```python
@dataclass
class ImpactResult:
    """变更影响分析结果。"""
    direct: list[str]          # 直接受影响的节点 id
    transitive: list[str]      # 间接受影响的节点 id（二级及以上）
    paths: dict[str, list[str]]  # 影响传播路径：affected_node → [path from change]
    depth: int                 # 分析深度
```

### 耦合标注（CouplingAnnotation）

```python
@dataclass
class CouplingAnnotation:
    """描述一组位置之间的语义耦合关系。"""
    id: str                      # 唯一标识
    description: str             # 耦合原因说明
    anchors: list[CouplingAnchor]  # 耦合的位置列表
    severity: str                # "must-sync" | "should-check" | "info"
    
@dataclass
class CouplingAnchor:
    """耦合标注中的一个位置。"""
    file_path: str
    symbol: str | None           # 可选：具体符号
    line_pattern: str | None     # 可选：行内容模式匹配
```

### 联动提醒（CouplingAlert）

```python
@dataclass
class CouplingAlert:
    """变更触发的联动提醒。"""
    annotation_id: str
    description: str
    severity: str
    triggered_by: str            # 触发源（文件或符号）
    check_targets: list[CouplingAnchor]  # 需要检查的其他位置
```

## 模块结构

```
tools/dependency_graph/
├── model.py           # (Slice 1) 已有
├── discovery.py       # (Slice 1) 已有
├── aggregator.py      # (Slice 1) 已有
├── query.py           # (Slice 1) 已有 — 扩展 impact_of / coupling_check
├── impact.py          # [新] ImpactAnalyzer — 变更影响传播
├── coupling.py        # [新] CouplingAnnotation 模型 + CouplingStore + CouplingChecker
└── coupling_annotations.json  # [新] 本仓库的耦合标注数据
```

## 验证门

- [x] ImpactAnalyzer 能从变更集沿图谱传播，正确计算直接和间接影响（7 unit tests）
- [x] CouplingAnnotation 数据模型可创建、序列化/反序列化、增删查（5 unit tests）
- [x] CouplingChecker 能匹配变更集与耦合标注，生成正确的 alert（4 unit tests）
- [x] dogfood：修改 WorkerBackend → 影响分析列出 ≥4 依赖模块（test_impact_of_worker_backend passed）
- [x] dogfood：标注 5 个本仓库耦合对，ErrorInfo/版本触发验证通过（3 dogfood tests）
- [x] 测试通过数 872 ≥ 基线 850（872 passed, 2 skipped）

## 风险

1. **传播深度控制**：无限深度传播可能导致整个图谱都被标为"受影响"；需要合理默认深度（建议：2）
2. **文件→符号映射**：变更集通常是文件级别，需要映射到图谱中的符号节点；Slice 1 的图谱已有 file_path 字段可用于此映射
3. **耦合标注维护成本**：手工维护耦合标注可能被遗忘；但这是不可避免的人工知识输入

## 后续切片预览（不在本切片范围）

- Slice 3：MCP + governance 集成 — `impact_analysis` / `coupling_check` MCP 工具 + `check_constraints` 联动
