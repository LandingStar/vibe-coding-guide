# Planning Gate — User-Global Pack Kind

> 创建时间: 2026-04-20
> 状态: DONE
> 前置: 无（现有 pack 系统已稳定）
> 方向分析: `design_docs/global-memory-docs-rules-direction-analysis.md` 候选 A

## 目标

扩展 pack kind 枚举，新增 `user-global` 类型。用户可在主目录下放置跨工作区生效的 pack，Pipeline 自动发现并按优先级合并。

## 设计决策（已确认）

1. **用户主目录路径**: `Path.home() / ".doc-based-coding" / "packs"`，支持 `DOC_BASED_CODING_USER_DIR` 环境变量覆盖
2. **优先级**: `platform-default(0) < official-instance(1) < user-global(2) < project-local(3)`
3. **冲突解决**: project-local 总是胜出（与现有 precedence 语义一致）
4. **迁移**: P0 不强制迁移，用户可选择性将个人约束写入 user-global pack

## Scope

### 必做

- [x] `src/pack/manifest_loader.py` — kind 枚举扩展
  - `_KIND_PRIORITY` 新增 `"user-global": 2`
  - 现有 `"project-local"` 从 `2` 调整为 `3`
  - `PackManifest` 的 kind validation 接受 `"user-global"`

- [x] `src/workflow/pipeline.py` — 用户主目录发现
  - 新增 `_user_global_dir() -> Path | None` 函数
    - 读取 `DOC_BASED_CODING_USER_DIR` 环境变量（如设置）
    - 否则使用 `Path.home() / ".doc-based-coding"`
    - 返回 `<dir> / "packs"` 路径（如存在）
  - `_discover_packs()` 在 workspace packs 之前扫描用户主目录
  - 用户主目录 pack 如未声明 kind，默认视为 `"user-global"`

- [x] `src/pack/context_builder.py` — 合并链确认
  - 验证 `build()` 的 kind priority 排序已自动适配新枚举（应无需改动，因为排序基于 `_KIND_PRIORITY` dict）

- [x] `docs/pack-manifest.md` — 文档更新
  - kind 表格新增 `user-global` 行
  - 新增 "User-Global Pack" 用法节

- [x] 测试（14 passed, tests/test_user_global_pack.py）
  - [x] 用户主目录 pack 发现（目录存在/不存在/环境变量覆盖）
  - [x] kind priority 排序（user-global 在 official-instance 和 project-local 之间）
  - [x] project-local 规则覆盖 user-global 规则
  - [x] user-global pack 的 always_on 内容在 ContextBuilder 输出中可见
  - [x] 跨平台路径测试（monkeypatch Path.home）

### 不做（后续 slice）

- 用户主目录配置文件 `config.json`（候选 C / P1）
- 记忆持久化（P1）
- 模板目录（P1）
- VS Code Extension 管理 UI（候选 D / P2）
- user-global 规则的不可覆盖标记
- `pack install --global` CLI 支持

## 验证标准

1. `~/.doc-based-coding/packs/` 下放置一个 `user-global.pack.json`（kind: user-global），Pipeline 能发现并加载
2. 同一 constraint 在 user-global 和 project-local 都声明时，project-local 胜出
3. user-global 的 always_on 内容出现在 InstructionsGenerator 输出中
4. 目录不存在时静默跳过，无报错
5. `DOC_BASED_CODING_USER_DIR=/custom/path` 时使用自定义路径

## 依据

- `design_docs/global-memory-docs-rules-direction-analysis.md` — 方向分析
- `design_docs/Project Master Checklist.md` — "全局记忆/文档/规则支持" 待办
- `.codex/handoffs/history/2026-04-19_0337_b-ref-series-close_stage-close.md` — Next Step Contract
