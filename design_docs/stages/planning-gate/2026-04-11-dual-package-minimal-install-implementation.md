# Planning Gate — Post-v1.0 Dual-Package Minimal Install Implementation

- Status: **COMPLETED**
- Date: 2026-04-11

## 问题陈述

`design_docs/tooling/Dual-Package Distribution Standard.md` 已经固定了“双发行包”的职责边界、安装入口归属、安装态 MCP 接入原则、最小兼容关系与最小验证门，但当前仓库仍停留在源码工作区形态：

1. 平台 runtime 还没有正式分发包元数据与安装后入口。
2. 官方实例 `doc-loop-vibe-coding/` 仍是仓库内资产目录，不是可安装官方实例包。
3. adoption 相关脚本虽已存在，但它们还没有被放进明确的安装态入口与 package data 布局中。

用户已确认，post-v1.0 的首个实现方向是“双发行包实现切片”，并同意只把构建后端、package data 和入口命名的窄调研交给子 agent，主 agent 继续负责 planning-gate、实现集成与 write-back。

## 审核后边界

用户已确认：

- 本轮先做“最小可安装实现”，不扩展到 registry、marketplace、远程拉取或自动化发布流水线。
- 继续遵守双发行包边界：平台 runtime 包与官方实例包分别发布。
- 子 agent 只负责只读窄调研，不负责共享状态文档、权威标准文档与最终实现写回。

## 权威输入

- `design_docs/tooling/Dual-Package Distribution Standard.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/Project Master Checklist.md`
- `docs/project-adoption.md`
- `docs/pack-manifest.md`
- `src/__main__.py`
- `src/mcp/server.py`
- `doc-loop-vibe-coding/pack-manifest.json`
- `doc-loop-vibe-coding/scripts/`

## 本轮只做什么

### Slice A: 分发骨架与入口归属落地

- 为平台 runtime 包补齐最小分发元数据。
- 为官方实例包补齐最小分发元数据。
- 明确并实现 runtime CLI 入口、runtime MCP 入口、官方实例 bootstrap/validate 入口。

### Slice B: 官方实例 package data 与资产发现

- 让官方实例 manifest、templates、prompts、references、examples、scripts 能在安装态被稳定发现。
- 避免安装态继续依赖发布者源码工作区相对路径。

### Slice C: 最小安装验证

- 增加最小 smoke 验证，覆盖 runtime CLI 入口、runtime MCP 入口、官方实例专属入口。
- 验证当前实现至少满足“双发行包标准”中的 clean environment / runtime smoke 的最小子集。

## 本轮明确不做什么

- 不重命名当前 `src` import root
- 不做远程 registry / marketplace 设计
- 不做自动化发布流水线
- 不在本轮完成完整兼容矩阵
- 不在本轮收口 script-style validator 的全部长期协议

## 验收与验证门

- 能从安装元数据层区分 runtime 包与官方实例包
- runtime CLI 与 MCP server 有明确、可安装的入口
- 官方实例 bootstrap / validate 入口有明确、可安装的入口
- 官方实例关键资产可在安装态被稳定发现
- 至少存在一组最小 smoke 验证覆盖上述入口和资产发现

## 执行结果

- root 新增 `pyproject.toml`，将 runtime 包固定为 `doc-based-coding-runtime`，并声明 `doc-based-coding` / `doc-based-coding-mcp` 两个安装入口。
- `doc-loop-vibe-coding/` 新增独立 `pyproject.toml`、`MANIFEST.in`、包标记文件与脚本包标记，形成官方实例包最小分发骨架。
- `validate_instance_pack.py` 现在在未显式传 `--target` 时，默认校验已安装包根或源码包根，适配安装态入口。
- 新增 `tests/test_dual_package_distribution.py`，覆盖 runtime/official-instance 分发元数据、包根辅助逻辑与实例自检默认根路径。
- 本地 wheel build smoke 已通过：runtime 包与官方实例包都能成功构建 wheel。

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `.codex/checkpoints/latest.md`

## 子 agent 切分草案

- 子 agent 只做三类只读调研：Python build backend、package data 打包方式、安装后入口命名方案。
- 主 agent 负责选择方案、实施代码修改、维护 planning-gate 与共享状态文档。

## 收口判断

- 当 runtime 包与官方实例包都具备最小安装骨架、入口归属清晰、资产发现可用，并且存在最小 smoke 验证时，本 planning-gate 可收口。
- 之后再决定是否进入“validator/check 契约收口”或“兼容元数据声明”切片。