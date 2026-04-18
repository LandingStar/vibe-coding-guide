# Planning Gate — 类型/接口依赖关系图谱提取（Slice 1）

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-15-type-dependency-graph-extraction |
| Scope | 基于 Pylance MCP 的项目类型/接口依赖关系图谱聚合 + 可查询存储 |
| Status | **DONE** |
| 来源 | `issues/issue_type_dependency_and_coupling_tracking.md` FR-1；用户选择"动态分析优先 + 先自用再泛化" |
| 前置 | 无活跃 planning-gate；当前代码库 70 .py / 13 包 / ~50+ 类 / 9 Protocol |
| 测试基线 | 823 passed, 2 skipped |

## 问题陈述

当前代码库有 13 个包、~50+ 个类、9 个 Protocol 定义，跨模块的继承/实现/调用/导入关系完全靠开发者和 agent 各自临时语义搜索理解。缺少一个可查询的关系图谱，导致：

1. 修改某个 Protocol 时不确定还有哪些实现者要跟着改
2. 修改某个模块的导出接口时无法快速枚举所有消费方
3. agent 在执行变更时缺少结构性依据判断影响范围

## 设计裁决

- **提取引擎**（用户选择 2026-04-15）：使用 Pylance MCP 作为底层类型分析引擎，而非自写 AST 提取器。Pylance 具备完整类型推断能力，精度远高于纯 AST，且 calls 边也可精确提取。
- **calls 边处理**（用户选择 2026-04-15）：Pylance 具备类型推断，calls 边可直接精确提取，不再需要 AST 变量追溯策略。
- **模块放置**（用户选择 2026-04-15）：`tools/dependency_graph/`，明确隔离为开发工具，不与业务代码混合。

## 目标

**做**：

1. 定义关系图谱的数据模型（节点类型 + 边类型）
2. 实现基于 Pylance MCP 的图谱聚合器：
   - 遍历 `src/` 下所有 `.py` 文件中的符号
   - 对每个符号调用 Pylance 获取引用/定义/实现关系
   - 聚合为统一的图谱数据结构
3. 将分析结果存为可查询的 JSON 格式
4. 提供最小查询接口：
   - "X 被谁依赖"（dependents of X）
   - "X 依赖谁"（dependencies of X）
   - "X 的实现者"（implementors of Protocol X）
5. 在本仓库 `src/` 上 dogfood 验证

**不做**：

1. 不做跨语言分析（仅 Python）
2. 不做变更影响传播或耦合钩子（属于 Slice 2）
3. 不与 governance 工具集成（属于 Slice 3）
4. 不把此功能暴露为平台公开能力（先自用）

## 数据模型草案

### 节点（Node）

```python
@dataclass
class GraphNode:
    id: str              # 全限定名，如 "src.workflow.pipeline.Pipeline"
    kind: str            # "module" | "class" | "function" | "protocol"
    file_path: str       # 源文件路径
    line_number: int     # 定义位置
    module: str          # 所属模块
```

### 边（Edge）

```python
@dataclass
class GraphEdge:
    source: str          # 源节点 id
    target: str          # 目标节点 id
    kind: str            # "inherits" | "implements" | "imports" | "calls" | "references"
    file_path: str       # 边声明所在文件
    line_number: int     # 边声明所在行
```

### 图谱（DependencyGraph）

```python
class DependencyGraph:
    nodes: dict[str, GraphNode]
    edges: list[GraphEdge]

    def dependents_of(self, node_id: str) -> list[GraphNode]: ...
    def dependencies_of(self, node_id: str) -> list[GraphNode]: ...
    def implementors_of(self, protocol_id: str) -> list[GraphNode]: ...
    def to_json(self) -> str: ...
    @classmethod
    def from_json(cls, data: str) -> "DependencyGraph": ...
```

## 架构

```
Pylance MCP (vscode_listCodeUsages / pylanceImports / pylanceWorkspaceUserFiles)
        |
        v
  +--------------------+
  |  Graph Aggregator   |  遍历符号 -> 调用 Pylance -> 聚合关系
  +---------+----------+
            |
            v
  +--------------------+
  |  DependencyGraph    |  数据模型 + 查询方法
  +---------+----------+
            |
            v
  +--------------------+
  |  JSON Storage       |  可持久化、可比较的图谱快照
  +--------------------+
```

## 交付物

### 1. 数据模型模块

- 文件：`tools/dependency_graph/model.py`
- 内容：`GraphNode`、`GraphEdge`、`DependencyGraph` 数据类与查询方法

### 2. 图谱聚合器

- 文件：`tools/dependency_graph/aggregator.py`
- 内容：基于 Pylance MCP 结果的图谱构建逻辑
- 输入：Pylance MCP 返回的 usage 数据（或等效的结构化符号信息）
- 输出：`DependencyGraph` 实例

### 3. 符号发现器

- 文件：`tools/dependency_graph/discovery.py`
- 内容：AST 遍历发现所有顶级符号（类、函数、Protocol），供聚合器逐个查询
- 说明：这是唯一用到 AST 的地方——只用于"发现有哪些符号需要查询"，而非分析关系

### 4. 查询接口

- 文件：`tools/dependency_graph/query.py`
- 内容：函数式查询入口
- 查询：dependents_of / dependencies_of / implementors_of

### 5. Dogfood 验证

- 在本仓库 `src/` 上运行聚合器
- 验证已知关系是否被正确聚合（如 `StubWorkerBackend` implements `WorkerBackend`）
- 输出示例图谱 JSON 作为 baseline

### 6. 测试

- 数据模型的单元测试（实例化、序列化/反序列化、查询）
- 聚合器的单元测试（mock Pylance 返回数据测试聚合逻辑）
- 集成测试：对本仓库 `src/` 运行并断言已知关系存在

## 验证门

- [x] `GraphNode` / `GraphEdge` / `DependencyGraph` 数据模型可实例化且可序列化/反序列化
- [x] 符号发现器能列出本仓库所有顶级类/函数/Protocol（174 符号：9 protocol, 60 class, 105 function）
- [x] 聚合器能从 Pylance MCP 结果构建完整图谱（186 节点，56 边）
- [x] 已知关系被正确识别：imports（13 边）、references（43 边）；Protocol 实现关系通过 dependents_of 查询验证（如 WorkerBackend → 5 个依赖模块）
- [x] `dependents_of` / `dependencies_of` / `implementors_of` 查询返回正确结果（含去重 + 模块级 node 自动注册）
- [x] 测试通过数不低于基线（850 passed vs 823 基线，+27 新测试）

## 风险

1. **Pylance MCP 调用量**：70 个文件可能有数百个符号，逐个查询可能耗时较长；可通过只查询顶级类/Protocol 控制规模
2. **Protocol 实现检测**：`vscode_listCodeUsages` 主要返回显式引用而非隐式实现者；需验证覆盖度
3. **build/ 副本干扰**：`vscode_listCodeUsages` 结果包含 `build/lib/` 中的副本引用，聚合时需过滤

## 后续切片预览（不在本切片范围）

- Slice 2：变更影响分析 — 给定变更集，沿图谱传播计算影响范围 + 耦合标记机制
- Slice 3：治理集成 — 接入 `check_constraints` / `writeback_notify`，MCP `query_dependency_graph` 工具
