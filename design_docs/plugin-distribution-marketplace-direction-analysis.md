# 方向分析 — Plugin Distribution / Marketplace 演化路径

## 背景

`review/research-compass.md` 最后一个未关闭研究空白。当前平台 v1.0 的 pack 分发与发现机制完全基于本地文件系统（convention scanning + 显式路径），无远程注册表、无包索引发布、无 marketplace 概念。

本文仅做方向分析与候选方案评估，**不进入实现**。

## 现状摘要

| 维度 | 现状 | 来源 |
|------|------|------|
| 分发方式 | 本地 wheel / 源码安装 | `docs/installation-guide.md` |
| 发现模式 | 文件系统 convention scan + `.codex/platform.json` 显式路径 | `src/workflow/pipeline.py` `_discover_packs()` |
| 版本校验 | `manifest_version` major 不匹配→拒绝，minor→警告；`runtime_compatibility` advisory | `src/pack/manifest_loader.py` |
| 依赖校验 | `depends_on` warning-only | `src/pack/manifest_loader.py` `check_dependencies()` |
| 注册表 | 无；仅 runtime 内部 `ValidatorRegistry` / `TriggerDispatcher` | `src/pack/registrar.py` |
| 远程解析 | 无 | — |

## 架构约束（设计必须遵守）

1. **双包边界守恒** — runtime 包保持 instance-neutral；marketplace 不得混淆 runtime 与 instance 分发（`design_docs/tooling/Dual-Package Distribution Standard.md`）
2. **Pack Tree 单继承** — 当前树模型要求线性 parent 链，marketplace 解析不得引入环或多继承（`src/pack/pack_tree.py`）
3. **Manifest 驱动优先级** — kind + insertion order 决定优先级，marketplace 不能引入运行时后协商（`src/pack/context_builder.py`）
4. **版本感知 loader** — major 不匹配硬拒绝，marketplace 必须在客户端执行 schema version 契约（`src/pack/manifest_loader.py`）
5. **Local-first 约定** — 文件系统 convention 是默认路径，远程注册表必须 opt-in 而非 default（当前 `.codex/platform.json` 已预留扩展点）

## 候选方案

### 方案 A — Pack Index Metadata（最小可行）

**思路**：不引入在线 marketplace，仅定义 pack 索引 metadata 格式与离线包交换流程。

**内容**：
- 定义 `pack-index.json` 格式：name / version / kind / runtime_compatibility / checksum / download_url
- 在 `.codex/platform.json` 新增 `pack_index` 字段指向本地或远程 index URL
- `manifest_loader` 新增 `resolve_from_index()` ：读取 index → 检查版本兼容 → 下载 → 放入 `pack_dirs`
- 签名/校验可选（checksum 即可）

**优点**：
- 不引入在线服务依赖
- 与现有 convention scan 完全兼容
- 可用于团队内部私有包交换
- 复杂度极低

**缺点**：
- 不支持搜索、评分、分类等 marketplace 特征
- 无自动更新 / 通知机制

**依据**：当前 `.codex/platform.json` 已有 `pack_dirs` 字段可自然扩展；`design_docs/tooling/Dual-Package Distribution Standard.md` 定义的双包模型不受影响。

### 方案 B — 本地 Registry Service（中等复杂度）

**思路**：在 runtime 内嵌一个轻量级本地 registry，支持 pack 注册、查询、版本解析。

**内容**：
- `src/pack/registry.py` — `PackRegistry` 类，SQLite 后端
- 支持 `register(manifest_path)` / `search(query)` / `resolve(name, version_constraint)` / `list()`
- CLI 新增 `doc-based-coding pack install <path>` / `pack list` / `pack search <query>`
- MCP 新增 `pack_search()` / `pack_install()` 工具
- 版本约束解析（semver range matching）

**优点**：
- 提供标准化的包管理体验
- 为远程 marketplace 奠定本地基础
- 支持多版本共存与切换

**缺点**：
- 引入 SQLite 依赖
- 需要处理包生命周期（install / uninstall / upgrade）
- 与现有 convention scan 需要协调优先级

**依据**：`review/research-compass.md` 提及 Semantic Kernel 的 OpenAPI/MCP plugin sources 可作为借鉴；Backlog BL-3 multi-protocol adapter 为此方案的远期延伸。

### 方案 C — 远程 Marketplace（全功能）

**思路**：搭建独立的 pack marketplace 服务，支持发布、搜索、评分、依赖解析。

**内容**：
- 独立服务（REST API）：pack 注册 / 版本管理 / 搜索 / 分类 / 下载
- 客户端 SDK 嵌入 runtime：`resolve_from_marketplace()` → 版本协商 → 下载 → 验证 → 安装
- manifest 签名与信任链
- 用户评价 / 下载统计 / 兼容性矩阵
- CI/CD 发布流水线（GitHub Actions → marketplace upload）

**优点**：
- 完整的生态系统体验
- 支持社区贡献与第三方 pack
- 可实现自动更新与安全通知

**缺点**：
- 需要独立基础设施与运维
- 超出当前项目范围（v1.0 后首批 dogfood 用户为自用场景）
- 信任模型复杂（谁可以发布？如何审核？）
- 投入大而当前用户基数不足以回收

**依据**：`design_docs/direction-candidates-after-phase-35.md` 明确标记 Plugin Distribution / Marketplace 为 deferred post-v1.0；当前无外部用户信号驱动。

## 推荐

| 阶段 | 方案 | 触发条件 |
|------|------|---------|
| 短期（当前） | **方案 A — Pack Index Metadata** | 当首次出现需要跨项目 / 跨机器共享 pack 的 dogfood 信号时 |
| 中期 | **方案 B — 本地 Registry** | 当方案 A 的手动流程在 3+ 个项目中产生可度量的摩擦时 |
| 远期 | **方案 C — 远程 Marketplace** | 当有 5+ 外部用户 / 团队实际使用平台，且方案 B 无法满足分发需求时 |

**当前判断**：鉴于平台处于 v1.0 post-release dogfood 阶段、唯一用户是项目自身，三个方案均 **不建议立即进入 planning-gate**。本分析文档作为储备，等待 dogfood 过程中出现分发需求信号后再行启动。

## 参考来源

- `docs/installation-guide.md`
- `docs/pack-manifest.md`
- `design_docs/tooling/Dual-Package Distribution Standard.md`
- `design_docs/tooling/Backlog and Reserve Management Standard.md` — BL-3
- `design_docs/direction-candidates-after-phase-35.md` — §31
- `review/research-compass.md` — Semantic Kernel plugin sources 借鉴
- `src/workflow/pipeline.py` — `_discover_packs()`
- `src/pack/manifest_loader.py` — version-aware loader
