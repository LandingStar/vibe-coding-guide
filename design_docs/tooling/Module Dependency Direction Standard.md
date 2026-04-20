# Module Dependency Direction Standard

> 来源：Multica 借鉴洞察 2.3 — pack/ → workflow/ → mcp/ 单向依赖

## 目标

确保 `src/` 内各子包的 import 方向遵循分层架构，避免循环依赖和隐式耦合。

## 分层定义

从底层到高层排列：

```
Layer 0 (Leaf)       interfaces, audit, review, validators, workers, adapters
Layer 1 (Core)       pack, collaboration, subagent
Layer 2 (Policy)     pdp, pep
Layer 3 (Orchestration) workflow
Layer 4 (Facade)     runtime
Layer 5 (Surface)    mcp
Layer 6 (Entry)      __main__, cli
```

## 基本规则

1. **向下依赖**：高层可以 import 低层或同层（`mcp → workflow → pack`）。
2. **禁止向上依赖**：低层不得 import 高层（`pack` 不应 import `workflow`、`mcp`）。
3. **同层互引须受控**：同层之间的互引应通过将共享类型/常量提取到 `interfaces.py`（Layer 0）来隔离。当前无已知例外。
4. **Layer 0 不得引用 Layer 1+**：`interfaces`、`audit` 等叶子模块保持零上游依赖。

## 已知例外与消除计划

| 违规 | 文件 | 导入目标 | 类型 | 状态 |
|------|------|---------|------|------|
| ~~pack → workflow~~ | ~~`pack/pack_manager.py:144`~~ | ~~`workflow.pipeline._discover_packs`~~ | ~~反向（L1→L3）~~ | ✅ 已消除：`_discover_packs` 下沉到 `pack/pack_discovery.py` |
| ~~pack → pdp (types)~~ | ~~`pack/override_resolver.py:9`~~ | ~~`pdp.tool_permission_resolver`~~ | ~~同层互引~~ | ✅ 已消除：`ToolPermissionConfig` 等类型提取到 `interfaces.py` |
| ~~pack → pdp (constants)~~ | ~~`pack/override_resolver.py:49`~~ | ~~`pdp.intent_classifier`~~ | ~~同层互引（延迟导入）~~ | ✅ 已消除：`PLATFORM_INTENTS`/`IMPACT_TABLE`/`KEYWORD_MAP` 提取到 `interfaces.py` |

> **当前状态：零已知例外，`lint_imports.py` 通过且 `KNOWN_EXCEPTIONS` 为空集。**

## 验证

项目根目录的 `scripts/lint_imports.py` 提供自动化检查。运行方式：

```bash
python scripts/lint_imports.py
```

该脚本会扫描 `src/` 下所有 `.py` 文件的跨包 import，对比上述分层规则，
输出违规列表并以非零退出码报告。已知例外在脚本的 `KNOWN_EXCEPTIONS` 中登记。

## 新增模块指引

- 新建子包时，先确定其所属 Layer，在本文档的分层定义中登记。
- 若需跨层依赖不符合向下规则，必须先在本文档的"已知例外"表中记录，并附消除计划。
- PR review 时应检查 `lint_imports.py` 输出。
