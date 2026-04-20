# 全局记忆/文档/规则支持 — 方向分析

> 生成时间: 2026-04-20
> 来源: `design_docs/Project Master Checklist.md` 待办 + Handoff Next Step Contract
> 当前基线: 1161 passed, 2 skipped

## 1. 问题定义

当前 pack/governance 体系完全 workspace-scoped：

- 规则发现只扫描 `.codex/packs/`、子目录和 site-packages
- 3 种 pack kind（`platform-default` / `official-instance` / `project-local`）均以工作区为边界
- 用户偏好（对话风格、安全硬约束、git push 禁令等）无法跨工作区自动继承
- 跨项目复用的模板、提示词、检查脚本需要手动复制

这导致：

1. 每个新工作区必须重新配置相同的用户级约束
2. 跨项目积累的最佳实践无法自动生效
3. AI 在不同项目间丧失对用户偏好的记忆

## 2. 现有架构参考

### 2.1 当前 Pack 加载链

```
Pipeline._discover_packs()
  → .codex/platform.json (pack_dirs)
  → .codex/packs/*.pack.json
  → subdir/pack-manifest.json
  → site-packages (installed wheels)

ContextBuilder.build()
  → 按 kind priority 排序合并
  → platform-default(0) < official-instance(1) < project-local(2)
```

### 2.2 当前 VS Code Extension

- 用户设置 `docBasedCoding.llm.family`（全局生效）
- 工作区设置覆盖用户设置（VS Code 原生 scope 分离）
- Extension 启动时将配置传递给 MCP server

### 2.3 Multica 参考模式

| 模式 | 本项目对应 |
|------|----------|
| Multi-Workspace 隔离 | 已有：每个 workspace 独立 pack/governance |
| Reusable Skills（跨 workspace 复用） | **缺失**：技能/规则不能跨 workspace 自动继承 |
| Agent Profile（跨 workspace 身份） | 部分：`copilot-instructions.md` + VS Code user settings |
| Unified Runtimes | 不适用（本项目非 SaaS 架构） |

### 2.4 VS Code 原生 Copilot Memory

```
/memories/          — 用户级，跨 workspace
/memories/session/  — 会话级
/memories/repo/     — 仓库级
```

这个三层模型与本项目需要的 global/workspace 分层高度对齐。

## 3. 候选方向

### 候选 A: User-Global Pack Kind

在现有 pack 类型上新增 `user-global`：

- 新 kind 值 `user-global`，priority 介于 `official-instance`(1) 和 `project-local`(2) 之间
- 发现路径：`~/.codex/packs/` 或 `%APPDATA%/.codex/packs/`（跨平台）
- 合并语义：project-local 仍可覆盖 user-global

**优点**：最小架构变更，完全复用现有 ContextBuilder 合并链
**缺点**：只解决规则层面，不解决记忆和文档模板的跨 workspace 问题；需要定义用户主目录约定

**scope**: 小（预计 1 slice，~30 行核心改动）
**前置依赖**: 无

### 候选 B: VS Code Extension Settings 桥接

- Extension 在用户设置中存储全局 pack 引用路径
- Extension 启动 MCP 时注入用户级 pack 路径参数
- MCP server / Pipeline 新增 `user_pack_dirs` 初始化参数

**优点**：利用 VS Code 原生 user/workspace 设置分离
**缺点**：耦合 VS Code，CLI-only 场景无法使用；配置分散在 VS Code 设置中

**scope**: 中
**前置依赖**: Extension 架构

### 候选 C: Platform Config Layer（用户主目录配置）

新增 `~/.doc-based-coding/config.json`：

```json
{
  "user_pack_dirs": ["~/.doc-based-coding/packs"],
  "user_memory_dir": "~/.doc-based-coding/memory",
  "user_templates_dir": "~/.doc-based-coding/templates",
  "default_rules_overlay": {
    "constraints": ["..."]
  }
}
```

- Pipeline 在 workspace 发现之前先读取用户主目录配置
- 用户主目录 pack 作为 `user-global` kind 合并
- 记忆和模板通过独立路径提供

**优点**：可移植（CLI + MCP + Extension 均可使用）；关注点分离清晰
**缺点**：新增配置层；需要定义跨 OS 主目录约定

**scope**: 中（预计 2 slice）
**前置依赖**: 候选 A 的 kind 扩展

### 候选 D: 混合方案（C + B 桥接）

- **核心层**：用户主目录 Platform Config（候选 C）
- **Extension 桥接**：VS Code Extension 读取并可视化/管理用户主目录配置
- **CLI 原生支持**：CLI 直接读取用户主目录配置

**优点**：长期目标架构，所有入口面统一
**缺点**：总工作量最大

**scope**: 大（3+ slice，但可按层切割）
**前置依赖**: 候选 A + C

## 4. 优先级排序

| 优先级 | 方向 | 理由 |
|-------|------|------|
| P0 | 候选 A: user-global pack kind | 最小可行改动，立即解决跨 workspace 规则继承 |
| P1 | 候选 C: 用户主目录配置 | 为记忆/模板/非 pack 资产提供跨 workspace 基础 |
| P2 | 候选 D-bridge: Extension 管理 UI | 用户体验层，依赖 P0+P1 就位 |

推荐实施路径：A → C → D（渐进式，每步独立有价值）

## 5. 对比分析

### 与 Multica Skills 系统对比

Multica 的 Skills 是 server 管理的可复用知识单元，通过 PostgreSQL 持久化。本项目的 pack 是文件系统分布式的规则包。

**借鉴点**：Skills 的"解决方案自动复用"理念 → 用户级 pack 可以将成功的规则组合自动带到新项目
**差异**：本项目不依赖中心化 server，需要基于文件系统的分发

### 与 VS Code Copilot Memory 对比

Copilot Memory 已有 user/session/repo 三层。本设计的 user-global pack 是 **规则/规格层** 的对应物——Copilot Memory 存事实，user-global pack 存约束和规则。两者互补而非替代。

## 6. 开放问题

1. **跨平台主目录约定**：Windows `%APPDATA%` vs macOS/Linux `~/.config/`？建议遵循 XDG 但 Windows 用 `%APPDATA%`
2. **user-global pack 与 project-local 冲突解决**：project-local 总是胜出？还是某些 user-global 规则不可被覆盖？
3. **记忆持久化格式**：JSON Lines（与 decision log 一致）？Markdown（与 Copilot Memory 一致）？
4. **迁移路径**：现有 `copilot-instructions.md` 中的用户约束是否应迁移到 user-global pack？

## 7. 推荐下一步

起草 P0 planning-gate：`user-global pack kind` 实现。预计 scope：

- `src/pack/manifest_loader.py`：kind 枚举 + priority
- `src/pack/pipeline.py`：用户主目录发现
- `src/pack/context_builder.py`：合并链调整（如需）
- 测试：发现 + 合并 + 覆盖 + 跨平台路径
- 文档：`docs/pack-manifest.md` 更新 kind 表格
