# Dependency Baseline Generator Contract

## 文档定位

本文件定义 adopted workspace 若选择启用 dependency impact propagation，应如何创建和维护
`tools/dependency_graph/baseline_graph.json`。

它定义的是生成器与 runtime consumer 之间的合同，不是某一种语言的生成器实现。

本合同不改变初始化行为：bootstrap 后的工作区可以没有 baseline。缺少 baseline 时，
`impact_analysis` / `analyze_changes` 的 impact section 应继续降级为“依赖传播不可用”，
而不是自动生成 baseline。

## 角色分工

- Runtime consumer
  - 读取 `tools/dependency_graph/baseline_graph.json`
  - 使用 `DependencyGraph.from_json(...)` 解析 `nodes` 与 `edges`
  - 运行 `query_impact(...)` 等查询
  - 缺少 baseline 时报告降级，不负责生成

- Workspace-local generator
  - 属于目标工作区或项目级 pack
  - 可以由 Python、TypeScript、语言服务器、构建系统或外部工具实现
  - 必须可复现地产出本合同定义的 baseline JSON
  - 必须记录覆盖范围、工具链和诊断信息，便于 agent 判断可信度

- Agent
  - 普通实现任务中不得手写或伪造 baseline
  - 只有当前 planning-gate 明确要求创建、刷新或维护 baseline 时，才运行 generator
  - 若 impact propagation 依赖 baseline 但 baseline 缺失或过期，应在结论中说明限制

## 文件位置

标准输出路径：

```text
tools/dependency_graph/baseline_graph.json
```

工作区可以另外保存 generator 源码、配置或日志，但 runtime consumer 的默认读取入口仍是上述路径。

## 最小 JSON 形状

baseline JSON 必须至少包含：

```json
{
  "nodes": {
    "module.symbol": {
      "id": "module.symbol",
      "kind": "function",
      "file_path": "src/module.py",
      "line_number": 10,
      "module": "src.module"
    }
  },
  "edges": [
    {
      "source": "src.consumer.use_symbol",
      "target": "src.module.symbol",
      "kind": "references",
      "file_path": "src/consumer.py",
      "line_number": 24
    }
  ]
}
```

当前兼容节点字段：

- `id`: 稳定节点 ID。建议使用语言内可读的全限定符；若语言没有稳定符号路径，generator 必须文档化 ID 规则。
- `kind`: 当前 runtime 兼容值为 `module`、`class`、`function`、`protocol`。
- `file_path`: 相对 workspace root 的路径，使用 `/` 或可被 `Path` 兼容解析的形式。
- `line_number`: 1-based 定义行号；未知时 generator 应尽量给出最接近的声明行，并在 diagnostics 说明覆盖限制。
- `module`: 节点所在模块或包的稳定名称。

当前兼容边字段：

- `source`: 源节点 ID。
- `target`: 目标节点 ID。
- `kind`: 当前 runtime 兼容值为 `inherits`、`implements`、`imports`、`calls`、`references`。
- `file_path`: 关系出现的位置；若关系来自项目级配置或外部图导出，写入最接近的来源路径。
- `line_number`: 1-based 行号；未知时写入 `0` 并在 diagnostics 说明。

## Metadata 扩展

generator 可以在顶层加入 `metadata`。现有 runtime consumer 会忽略未知顶层字段，因此这不会破坏当前
`DependencyGraph.from_json(...)`。

推荐 metadata：

```json
{
  "metadata": {
    "contract": "dependency-baseline-generator-contract",
    "contract_version": "0.1",
    "generator_id": "project-python-pylance-baseline",
    "generator_version": "0.1.0",
    "created_at": "2026-06-08T00:00:00Z",
    "workspace_root_policy": "paths relative to workspace root",
    "source_coverage": {
      "include": ["src/**/*.py"],
      "exclude": ["build/**", ".venv/**"],
      "languages": ["python"]
    },
    "toolchain": [
      {"name": "pylance", "version": "documented-or-unknown"}
    ],
    "diagnostics": []
  }
}
```

metadata 不能替代 `nodes` / `edges`。它只用于解释生成过程、覆盖范围和可信度。

## 稳定性要求

generator 输出必须尽量稳定：

- 节点 ID 规则必须文档化，并在同一符号未改名时保持不变。
- `nodes` 建议按 ID 排序。
- `edges` 建议按 `(source, target, kind, file_path, line_number)` 排序。
- 同一 source/target/kind/location 不应重复输出。
- 生成结果不得包含绝对本机路径、用户私有目录、临时构建目录或虚拟环境路径，除非项目显式把它们纳入分析范围。

## 覆盖范围与部分可信

generator 必须诚实表达覆盖范围。

允许部分覆盖，例如只覆盖 Python `src/`，或只覆盖 public API 层。但这种情况必须写入 metadata 或 generator 文档。

不得把部分覆盖 baseline 表述为全仓库完整影响图。

如果某些边类型无法可靠提取：

- 可以省略该类边
- 或降级为 `references`
- 但必须在 diagnostics 中说明

## Refresh 触发条件

应刷新 baseline 的情况：

- 模块布局、包路径或 public API 结构改变
- 影响依赖提取的工具链、配置或 include/exclude 规则改变
- generator 源码或输出合同改变
- 当前任务明确需要基于最新 dependency impact propagation 做风险判断

不应刷新 baseline 的情况：

- 仅为了消除缺 baseline 提示
- 与依赖结构无关的文案、样式、测试夹具或 release artifact 改动
- 当前 planning-gate 未把 baseline 创建/维护列入 scope

## 验证门

每个 generator 至少应提供以下验证：

1. JSON 可解析。
2. `DependencyGraph.from_json(...)` 可加载。
3. `graph.summary()` 返回非异常结果。
4. 至少一个已知节点能被查询。
5. 若生成器声称支持某种边类型，应有 fixture 或 smoke test 证明该边类型能出现。
6. 输出不包含应排除的路径，如 `.venv/`、`build/`、`node_modules/`。

对于 adopted workspace，最小 smoke 可以是：

```powershell
python - <<'PY'
from pathlib import Path
from tools.dependency_graph.model import DependencyGraph

path = Path("tools/dependency_graph/baseline_graph.json")
graph = DependencyGraph.from_json(path.read_text(encoding="utf-8"))
print(graph.summary())
PY
```

## 与 MCP 工具的关系

`impact_analysis` 和 `analyze_changes` 只消费 baseline。

它们不得在调用时自动生成 baseline，原因是：

- 自动生成可能很慢
- 生成器可能需要项目级工具链或宿主环境
- 当前任务未必授权修改 workspace artifact
- 旧 baseline 缺失与 generator 缺失是不同问题

缺少 baseline 时，MCP 应继续返回结构化降级信息。

## 与项目 adoption 的关系

bootstrap 不创建 baseline，也不强制项目启用 dependency impact propagation。

项目如果需要该能力，应在自己的 planning-gate 中声明：

- 是否启用 baseline
- 采用哪个 generator
- 覆盖哪些路径和语言
- 如何验证输出
- 何时刷新
- 谁负责在 write-back 中记录生成命令与结果

## 参考实现边界

当前仓库的 `tools/dependency_graph/build_baseline.py` 是历史 dogfood prototype，可作为 Python/Pylance 参考实现候选。

它不是本合同的通用标准，也不应被 adopted workspace 盲目复制。

后续若要把它整理成正式参考 adapter，应另起切片，至少完成：

- 与本合同字段对齐
- 去除本仓库硬编码路径
- 明确 include/exclude 配置
- 添加 fixture / smoke validation
- 文档化工具链前提
