# doc-based-coding v0.9.4 Release (2026-04-21)

架构合规性全面收口 + Worker schema 对齐 + 依赖方向零违规。

## 打包内容

| 产物 | 版本 | 说明 |
|------|------|------|
| `doc_based_coding_runtime-0.9.4-py3-none-any.whl` | 0.9.4 | 平台运行时，包含 CLI、MCP server、PDP/PEP、workflow、pack runtime |
| `doc_loop_vibe_coding-0.9.4-py3-none-any.whl` | 0.9.4 | 官方 doc-loop 实例 pack |
| `doc-based-coding-0.1.2.vsix` | 0.1.2 | VS Code 扩展 |

## 本次版本重点

### 1. 模块依赖方向强制

- 新增 Module Dependency Direction Standard（6 层架构 + 方向规则文档）
- 新增 `lint_imports.py` AST 自动化验证
- 3/3 跨层依赖违规全部消除（`pack_discovery.py` 下沉 + 常量提升到 `interfaces.py`）
- 当前零违规、零已知例外

### 2. HTTPWorker Schema 对齐

- `_error_report()` 输出与 LLMWorker / Subagent Report Schema 完全一致
- `status` enum 修正为 `"blocked"`，`escalation_recommendation` 修正为 `"review_by_supervisor"`
- 新增 `unresolved_items` 字段

### 3. B-REF 系列全部完成

- B-REF-1~7：渐进式加载、description 质量标准、pack 组织规范、permission policy、工作流中断原语、子 agent 上下文隔离评估、tool surface 合并审计

### 4. Multica 架构借鉴落地

- Pack Integrity Hash（`pack-lock.json` + `compute_pack_hash()`）
- 条件化 `always_on` 加载（`scope_path` 过滤）
- RuntimeBridge 三入口统一初始化 + WorkerHealth
- PackManifest `consumes` 字段 + 能力依赖校验

### 5. VS Code Extension 全功能

- P0-P7 功能完备 + 安装向导 + git push guard + Chat Participant
- 全局记忆/文档/规则支持

## 验证结果

- `pytest`：1257 passed, 2 skipped
- `lint_imports.py`：零违规
- `pack_verify`：2/2 packs ok
- VS Code Extension esbuild：零错误
- MCP 全工具链 dogfood 通过

## 安装顺序

```bash
pip install doc_based_coding_runtime-0.9.4-py3-none-any.whl
pip install doc_loop_vibe_coding-0.9.4-py3-none-any.whl
```

VS Code 扩展通过 "Install from VSIX" 安装 `doc-based-coding-0.1.2.vsix`。

完整变更历史见仓库根目录 `CHANGELOG.md`。
# doc-based-coding Snapshot Bundle (2026-04-19)

本次是基于当前工作区最新结果生成的快照发布包，不引入新的统一平台版本号；各组件继续沿用各自当前版本线。

## 打包内容

| 产物 | 版本 | 说明 |
|------|------|------|
| `doc_based_coding_runtime-0.9.3-py3-none-any.whl` | 0.9.3 | 平台运行时，包含 CLI、MCP server、PDP/PEP、workflow、pack runtime |
| `doc_loop_vibe_coding-0.9.4-py3-none-any.whl` | 0.9.4 | 官方 doc-loop 实例 pack |
| `doc-based-coding-0.1.2.vsix` | 0.1.2 | VS Code 扩展 |

对应压缩包文件名：`doc-based-coding-snapshot-2026-04-19.zip`。

## 本次快照重点

### 1. VS Code Extension

- 新增 `docBasedCoding.selectModel` 命令
- 新增 `docBasedCoding.llm.family` 配置项
- 配置变更后自动重新初始化 Copilot LLM provider

### 2. Permission Policy 分层覆盖

- 新增 `src/pdp/tool_permission_resolver.py`
- 支持 pack 级默认策略 + tool 级 override
- 权限合并规则固定为 `deny > ask > allow`
- `governance_decide()` 支持 `action_type` 输入并返回工具权限判定结果

### 3. 工作流中断原语

- 新增 `workflow_interrupt` MCP tool
- 返回结构化 `guidance`，用于在发现超出 scope 的问题时回退到 planning-gate
- 支持 decision log 记录 interrupt 事件

### 4. 子 agent 上下文隔离评估

- 完成 B-REF-6 评估报告
- 结论：当前三层模型“合同声明 -> Prompt 隔离 -> Subgraph delta merge”已经等效实现“共享工作区文件 + 隔离上下文”
- 当前无需架构级改造，仅建议后续补 `allowed_artifacts` 路径硬校验

## 验证结果

- `npm run build`（vscode-extension）通过
- `npx vsce package --no-dependencies` 通过
- `python scripts/build.py --skip-checks --no-isolation` 通过
- `pytest --tb=short -q`：1161 passed, 2 skipped

## 安装顺序

```bash
pip install doc_based_coding_runtime-0.9.3-py3-none-any.whl
pip install doc_loop_vibe_coding-0.9.4-py3-none-any.whl
```

VS Code 扩展通过 “Install from VSIX” 安装 `doc-based-coding-0.1.2.vsix`。

## 说明

- 本次 zip 是“最新构建快照包”，因此 zip 名称采用日期而不是统一平台语义版本。
- Python wheel 的构建使用了 `--skip-checks`，原因是 `release/README.md` 和旧安装文档仍保留较早发布口径，未纳入本次最小打包修正范围。
- 若后续要做正式 release，建议先统一 `release/README.md`、安装文档和版本一致性校验规则。

完整变更历史见仓库根目录 `CHANGELOG.md`。
