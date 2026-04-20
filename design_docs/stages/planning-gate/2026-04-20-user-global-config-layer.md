# Planning Gate — User-Global Config Layer (P1)

> 创建时间: 2026-04-20
> 状态: DONE
> 前置: P0 user-global pack kind (DONE)
> 方向分析: `design_docs/global-memory-docs-rules-direction-analysis.md` 候选 C

## 目标

在 `~/.doc-based-coding/config.json` 新增用户级配置文件，Pipeline 在 workspace 发现之前先读取。为记忆/模板/非 pack 资产提供跨 workspace 基础设施。

## 设计决策（待确认）

1. **配置文件位置**: `<user_dir>/config.json`（复用 P0 的 `_user_global_packs_dir` 路径约定）
2. **初始字段集**: 见下方 Scope
3. **缺失文件处理**: 文件不存在或 JSON 无效时返回空默认配置，不报错
4. **字段合并语义**: config 中的 `extra_pack_dirs` 追加到发现路径列表（不替换内置路径）

## Scope

### 必做

- [x] `src/pack/user_config.py` — 新模块
  - `UserConfig` dataclass: `extra_pack_dirs: list[str]`, `default_model: str | None`, `default_llm_params: dict`
  - `load_user_config(user_dir: Path | None) -> UserConfig` — 读取 config.json，缺失时返回默认
  - JSON schema 验证：仅接受已知字段 + unknown 忽略（前向兼容）

- [x] `src/workflow/pipeline.py` — 集成
  - `_discover_packs()` 在扫描 `~/.doc-based-coding/packs/` 后，追加扫描 `extra_pack_dirs` 中的路径
  - `Pipeline.from_project()` 将 `UserConfig` 存为 `self._user_config`
  - `Pipeline.info()` 新增 `user_config` 节

- [x] `docs/user-config.md` — 新文档
  - 配置文件路径和格式说明
  - 各字段含义与默认值
  - 跨 OS 行为说明

- [x] 测试（22 passed, tests/test_user_global_config.py）
  - [x] config.json 存在/不存在/无效 JSON/空文件
  - [x] extra_pack_dirs 的 pack 发现
  - [x] default_model / default_llm_params 读取
  - [x] Pipeline.info() 包含 user_config 节
  - [x] 未知字段前向兼容

### 不做（后续 slice）

- user_memory_dir / user_templates_dir（P1+ 或 P2）
- default_rules_overlay（需要设计与 pack rules 的合并语义）
- VS Code Extension config UI（候选 D / P2）
- config.json 的 hot-reload / file watcher

## 验证标准

1. `~/.doc-based-coding/config.json` 存在且包含 `extra_pack_dirs` 时，Pipeline 能发现该目录下的 pack
2. config.json 缺失或无效时静默降级，不影响现有工作流
3. `Pipeline.info()` 正确暴露 user_config 信息
4. 全量测试无回归

## 依据

- `design_docs/global-memory-docs-rules-direction-analysis.md` — 候选 C
- `design_docs/stages/planning-gate/2026-04-20-user-global-pack-kind.md` — P0 基础
- `design_docs/Project Master Checklist.md` — 全局记忆/文档/规则支持待办
