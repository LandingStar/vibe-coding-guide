# Dependency Baseline Maintenance Guide

## 文档定位

本文件说明 adopted workspace 如何使用 reference adapter 维护
`tools/dependency_graph/baseline_graph.json`。

合同定义见 `docs/dependency-baseline-generator-contract.md`。本文件只负责操作指导。

## 基本原则

- baseline 是可选工作区快照，不是 bootstrap 默认产物。
- agent 不得手写或伪造 baseline。
- MCP `impact_analysis` / `analyze_changes` 只消费 baseline，不负责生成。
- Python 项目应优先利用 Pylance usage 数据增强关系边；AST 只负责稳定符号骨架和少量保守关系。
- JavaScript 支持当前是 conservative reference support，不是完整调用图。

## Python + Pylance 推荐路径

Python reference adapter 的推荐输入是：

1. Python AST 符号发现：
   - module
   - class
   - function
   - Protocol
   - import
   - simple inheritance / implements
2. Pylance usage fixture：
   - 来自 `vscode_listCodeUsages` 或等效结构化输出
   - 用于补充 `imports`、`references`、`calls` 等关系

推荐 fixture 形状：

```json
{
  "vscode_listCodeUsages": [
    {
      "target": "src.api.Service",
      "usages": [
        {
          "usage_type": "reference",
          "file_path": "src/consumer.py",
          "line": 12,
          "line_content": "service: Service",
          "symbol": "Service"
        }
      ]
    }
  ]
}
```

兼容形状：

- `{ "symbols": { "<target-node-id>": [usage, ...] } }`
- `{ "pylance_usages": { "<target-node-id>": [usage, ...] } }`
- `{ "usages": [ { "target": "<target-node-id>", ... } ] }`

## Pylance Fixture 采集流程

当宿主能访问 VS Code / Pylance MCP 时，优先用 Pylance 采集关系数据，而不是让 adapter
猜测调用图。

推荐流程：

1. 先用 adapter 或现有 baseline 列出目标 Python 符号。
2. 对 public API、Protocol、跨模块服务类、核心函数调用 `vscode_listCodeUsages`。
3. 将每个符号的结果保存到 `tools/dependency_graph/pylance-usages.json`。
4. 运行 `refresh --pylance-usage-fixture tools/dependency_graph/pylance-usages.json`。
5. 运行 `validate` 并抽查关键符号的 `dependents_of` / `dependencies_of`。

采集优先级：

- Protocol / abstract interface
- public class
- public function
- package-level module exports
- 最近改动涉及的符号

不要为所有局部变量或私有 helper 盲目采集 Pylance usages；这会让 fixture 维护成本过高。

如果当前宿主无法调用 Pylance，agent 应记录：

- Pylance fixture unavailable
- 当前 baseline 是 AST fallback / partial coverage
- 后续应在 VS Code/Pylance 可用环境中补采集

## 创建

仅当当前 planning-gate 明确需要 baseline 时创建。

```powershell
python -m tools.dependency_graph.reference_adapter create `
  --project-root . `
  --language python `
  --pylance-usage-fixture tools/dependency_graph/pylance-usages.json
```

没有 Pylance fixture 时可以创建降级 baseline，但必须在 write-back 中说明：

- Python call/reference coverage 是部分可信
- 后续应补 Pylance usage fixture

## 刷新

当模块布局、public API、重要依赖关系、generator 配置或 Pylance fixture 改变时刷新。

```powershell
python -m tools.dependency_graph.reference_adapter refresh `
  --project-root . `
  --language python `
  --language javascript `
  --pylance-usage-fixture tools/dependency_graph/pylance-usages.json
```

`refresh` 默认备份旧 baseline，备份文件位于 baseline 同目录。

## 生成

`generate` 是低层生成命令，适合被脚本或外层工作流调用。普通 adopted workspace 维护时：

- 第一次落地 baseline 优先使用 `create`
- 日常更新优先使用 `refresh`
- 只有外层流程已经明确 overwrite / backup 策略时才直接使用 `generate`

```powershell
python -m tools.dependency_graph.reference_adapter generate `
  --project-root . `
  --language python `
  --language javascript `
  --pylance-usage-fixture tools/dependency_graph/pylance-usages.json
```

如需在低层命令中保留旧输出，显式加入 `--backup`。

## 验证

每次创建、刷新、修正或回退后都应验证。

```powershell
python -m tools.dependency_graph.reference_adapter validate --project-root .
python -m pytest tests/test_dependency_graph*.py tests/test_mcp_tools.py -q
```

最低验收：

- JSON 可解析
- `DependencyGraph.from_json(...)` 可加载
- `graph.summary()` 非异常
- 输出不包含本机绝对路径、`.venv/`、`build/`、`node_modules/`
- Pylance fixture 被使用时，metadata.toolchain 包含 `pylance-usage-fixture`

## 修正

当 baseline 仅存在机械问题时使用 `repair`：

- 绝对路径可归一化为 workspace-relative
- 重复边可去重
- 缺 endpoint 的边可删除

```powershell
python -m tools.dependency_graph.reference_adapter repair --project-root .
```

不要用 `repair` 掩盖真实覆盖缺口。缺少 Pylance usage、语言支持不足或 include/exclude 错误，应修 generator 或 fixture 后重新 refresh。

## 回退

当新 baseline 使 impact result 明显退化、引入路径污染或错误边时，先回退，再分析原因。

```powershell
python -m tools.dependency_graph.reference_adapter rollback `
  --path tools/dependency_graph/baseline_graph.json
```

如果要指定备份：

```powershell
python -m tools.dependency_graph.reference_adapter rollback `
  --path tools/dependency_graph/baseline_graph.json `
  --backup tools/dependency_graph/baseline_graph.20260610T120000000000Z.json.bak
```

## JavaScript 扩张

当前 JavaScript 支持适合先建立低风险 baseline：

```powershell
python -m tools.dependency_graph.reference_adapter refresh `
  --project-root . `
  --language javascript
```

覆盖范围：

- `.js`
- `.mjs`
- `.cjs`
- `.jsx`
- module node
- class/function node
- `import` / `require`
- simple `extends`

不覆盖：

- TypeScript compiler semantic graph
- Babel/SWC transform semantics
- dynamic import resolution
- framework-specific dependency injection
- full call graph

如果项目需要这些能力，应另起 planning-gate 扩展 adapter，而不是把 conservative output 当成完整影响图。

## Write-Back 要求

baseline 相关任务完成后，write-back 至少记录：

- 使用的命令
- 覆盖语言与 include/exclude
- 是否使用 Pylance fixture
- validation 结果
- 是否产生备份或执行回退
- 已知覆盖限制
