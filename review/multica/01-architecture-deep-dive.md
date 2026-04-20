# Multica 架构深度研究报告

> 分析日期: 2026-04-20
> 版本: v0.2.6 (16.7k stars, 2.1k forks, 54 contributors, 43 releases)
> 来源: https://github.com/multica-ai/multica
> 许可证: Modified Apache 2.0（内部使用自由，SaaS/转售受限，前端必须保留 logo 和版权）

---

## 1. 项目定位与产品形态

Multica 自称 "open-source managed agents platform"，核心理念是将 coding agent 视为**"真正的队友"**。

**产品形态三合一**：
- **Web App** (Next.js 16 App Router) — 托管版 multica.ai
- **Desktop App** (Electron + 内嵌 bundled CLI) — 独立客户端，自动管理 daemon
- **CLI** (`multica` 命令) — 终端操作 issue、agent、workspace、autopilot

**目标用户**: 2-10 人 AI-native 团队，"like Linear, but with AI agents as first-class teammates"

**支持的 Agent Runtime**（截至 v0.2.6）：
| Agent | 类型 | 备注 |
|-------|------|------|
| Claude Code | CLI | 支持 session resume / thread ID 续接 |
| Codex (OpenAI) | CLI | 支持 subagent threadId 过滤 |
| GitHub Copilot | CLI | v0.2.1 新增 |
| Cursor Agent | CLI | v0.2.1 新增 |
| OpenClaw | CLI | P0+P1 级支持 |
| OpenCode | CLI | - |
| Hermes | CLI | 自定义参数过滤 |
| Gemini CLI | CLI | live log 支持(stream-json) |
| Pi | CLI | pi.dev 图标 |

---

## 2. 系统架构全景

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户入口                                      │
│  ┌───────────┐  ┌──────────────┐  ┌───────────────┐               │
│  │  Web App  │  │ Desktop App  │  │  CLI (`multica`)│              │
│  │ (Next.js) │  │ (Electron)   │  │  (Go binary)  │               │
│  └─────┬─────┘  └──────┬───────┘  └───────┬───────┘               │
│        │               │                   │                        │
│        └───────────┬────┴───────────────────┘                      │
│                    ▼                                                 │
│  ┌──────────────────────────────────┐                              │
│  │         Go Backend Server         │                             │
│  │  (Chi Router + gorilla/websocket) │                             │
│  │  ┌─────────┐ ┌────────┐ ┌──────┐ │                             │
│  │  │ Handler │ │Service │ │ Auth │ │                             │
│  │  │  Layer  │→│ Layer  │ │(JWT) │ │                             │
│  │  └─────────┘ └───┬────┘ └──────┘ │                             │
│  │                   ▼               │                              │
│  │  ┌───────────────────────────┐    │                             │
│  │  │   sqlc Generated Queries  │    │                             │
│  │  └───────────┬───────────────┘    │                             │
│  └──────────────┼────────────────────┘                              │
│                 ▼                                                    │
│  ┌──────────────────────┐                                          │
│  │ PostgreSQL 17         │                                          │
│  │ + pgvector extension  │                                          │
│  │ (~25+ 业务表)          │                                          │
│  └──────────────────────┘                                           │
│                                                                     │
│  ┌──────────────────────────────────────┐                          │
│  │       Agent Daemon (本地运行)          │                          │
│  │  poll server 3s / heartbeat 15s      │                          │
│  │  max 20 concurrent / 2h timeout      │                          │
│  │  ┌──────────┐ ┌──────────┐ ┌──────┐ │                          │
│  │  │ execenv  │ │repocache │ │ GC   │ │                          │
│  │  │(sandbox) │ │(git ops) │ │      │ │                          │
│  │  └──────────┘ └──────────┘ └──────┘ │                          │
│  └──────────────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Go Backend 内部分层

**Handler 层** (`server/internal/handler/`, ~25 个文件)：

| 文件 | 职责 |
|------|------|
| `agent.go` | Agent CRUD、自定义参数、环境变量 |
| `autopilot.go` | 自动化任务调度 |
| `chat.go` | 实时聊天 |
| `comment.go` | Issue 评论（触发 agent 执行） |
| `daemon.go` | Daemon 注册、任务认领(ClaimTask)、心跳 |
| `issue.go` | Issue 生命周期 |
| `runtime.go` | Runtime 注册与管理 |
| `search.go` | 全局搜索(cmd+k) |
| `skill.go` | Skills CRUD |
| `trigger.go` | 事件触发器 |
| `workspace.go` | Workspace 管理 |

**数据访问层** (`server/pkg/db/queries/`, ~25 个 SQL 文件)：

使用 `sqlc` 从 SQL 文件直接生成类型安全的 Go 代码。主要表：

| 表/查询文件 | 对应领域 |
|------------|---------|
| `workspace.sql` | 多租户隔离根节点 |
| `agent.sql` | Agent 配置（name, runtime, custom_args, custom_env） |
| `runtime.sql` + `runtime_usage.sql` | 计算环境与用量追踪 |
| `issue.sql` | 核心任务单元 |
| `task_message.sql` + `task_usage.sql` | 任务执行消息与 token 使用 |
| `skill.sql` | Skills 存储 |
| `autopilot.sql` | 自动化规则 |
| `chat.sql` | 实时聊天历史 |
| `comment.sql` | Issue 评论 |
| `daemon_token.sql` | Daemon 认证 |
| `inbox.sql` | 通知收件箱 |
| `invitation.sql` | 团队邀请 |
| `member.sql` | 成员管理 |
| `project.sql` | 项目组织 |
| `attachment.sql` | 文件附件 |
| `subscriber.sql` | 订阅/关注 |
| `activity.sql` | 操作审计日志 |
| `pinned_item.sql` | 固定条目 |
| `personal_access_token.sql` | API Token |
| `verification_code.sql` | 验证码 |
| `reaction.sql` + `issue_reaction.sql` | 表情反应 |

### 2.2 Daemon 架构详解

**核心模块** (`server/internal/daemon/`)：

| 文件 | 职责 |
|------|------|
| `daemon.go` | 主循环：poll → claim → dispatch → report |
| `client.go` | 与 server 的 HTTP 通信 |
| `config.go` | daemon 配置（poll interval, heartbeat, timeout, max concurrent） |
| `identity.go` | 持久化 UUID（machine-scoped，CLI+Desktop 共享同一身份） |
| `health.go` | 健康检查 |
| `gc.go` | 垃圾回收（清理已完成/过时任务） |
| `helpers.go` | 辅助函数 |
| `prompt.go` | 构建注入 agent 的 prompt（CLAUDE.md 等） |
| `types.go` | 类型定义 |

**执行环境** (`server/internal/daemon/execenv/`)：

| 文件 | 职责 |
|------|------|
| `execenv.go` | 执行环境抽象（如何启动 agent 进程） |
| `context.go` | 上下文构建（注入 workspace context, skills） |
| `codex_home.go` | Codex 特定 home 目录管理 |
| `codex_sandbox.go` | Codex 沙箱配置（macOS network unbreak） |
| `git.go` | Git 操作（checkout, worktree isolation） |
| `runtime_config.go` | 平台感知的运行时配置（platform-aware sandbox） |

**Daemon 生命周期**：

1. **启动**: `multica daemon start` 或 Desktop App 自动启动
2. **注册**: 向 server 注册，获取 daemon token，建立持久 UUID 身份
3. **轮询**: 每 3 秒 poll server 获取待执行任务
4. **认领**: ClaimTaskByRuntime — 根据可用 agent runtime 认领匹配任务
5. **执行**: 在本地 worktree 中启动 agent CLI 进程
6. **心跳**: 每 15 秒向 server 报告任务存活状态
7. **完成**: 收集 agent 输出 → 上报 server → WebSocket 广播
8. **防卡**: 2h 超时自动终止 + stuck task 检测

**关键设计决策**：
- 每次任务在隔离的 git worktree 中执行
- Daemon 自动检测 PATH 上可用的 agent CLI
- 支持 per-agent MCP 配置（v0.2.6 新增）
- Desktop 版自动随 bundled CLI 版本重启 daemon
- 平台感知沙箱（macOS 解锁网络访问）

---

## 3. 前端 Monorepo 架构

### 3.1 仓库结构

```
multica/
├── apps/
│   ├── web/          # Next.js 16 App Router — 托管版
│   ├── desktop/      # Electron — 桌面客户端
│   └── docs/         # 文档站点 (mounted at /docs subpath)
├── packages/
│   ├── core/         # 零 DOM — headless 业务逻辑
│   ├── ui/           # 零业务逻辑 — atomic UI 组件
│   └── views/        # 零框架依赖 — 共享业务页面
├── server/           # Go backend
├── cmd/              # CLI (Go)
├── pnpm-workspace.yaml
└── turbo.json
```

### 3.2 Internal Packages 模式

**核心规则**: 共享包直接导出原始 `.ts/.tsx` 文件，不做任何预编译。消费方（apps）的 bundler 负责编译。

**好处**：
- 零配置 HMR（修改 core/ui/views 时 apps 自动热更新）
- 无需管理包的构建产物
- 类型检查和 lint 由 Turborepo 并行执行

**严格边界**：

```
core/          → 零 react-dom 依赖，纯业务逻辑
                  (API client, auth, WebSocket, state)
   ↓
ui/            → 零业务逻辑，atomic 组件
                  (Button, Dialog, Toast, ...)
   ↓
views/         → 零框架依赖，共享业务页面
                  (IssueDetail, AgentConfig, Workspace, ...)
   ↓
apps/web       → Next.js 特定：路由、SSR、middleware
apps/desktop   → Electron 特定：IPC、窗口管理、daemon
```

### 3.3 状态管理

| 分类 | 工具 | 用途 |
|------|------|------|
| Server State | React Query (TanStack Query) | API 数据缓存、乐观更新、自动重验证 |
| Client State | Zustand | UI 状态（sidebar 折叠、tab 切换、主题） |
| Real-time | WebSocket | WS 事件触发 React Query cache invalidation |

**严格规则**: 禁止在 Zustand store 中存储 server 数据，禁止在 React Query 中管理 UI 状态。

### 3.4 Platform Bridge

`CoreProvider` 初始化所有共享基础设施（API client, auth, WebSocket），每个 app 提供自己的 `NavigationAdapter` 适配路由系统。

Desktop 的特殊处理：
- 窗口管理: 多 tab + workspace 切换（tab 是 per-workspace 的）
- 预 workspace 流程建模为 window overlays（非 tab routes）
- traffic-light 空间预留
- Daemon 管理 panel（sidebar 状态栏）
- 应用共存: dev/production 实例可以并行运行（Multica Canary）

---

## 4. Skills 系统

### 4.1 概念

Skills = **可复用知识单元**，核心理念是 "every solution becomes a reusable skill for the whole team"。

Skills 不是代码执行单元，而是**提供给 agent 的上下文/指导文档**。

### 4.2 实现

**`skills-lock.json`** — 记录已安装的 skills：

```json
{
  "skills": [
    {
      "name": "frontend-design",
      "source": "https://github.com/anthropics/skills/tree/main/frontend-design",
      "sourceType": "github",
      "computedHash": "sha256-..."
    }
  ]
}
```

**存储与加载**：
- Skills 内容存储在数据库 `skill` 表中
- Daemon 在执行任务时，将 workspace 的 skills 注入到 agent 的 prompt/context 中
- 对 Copilot agent，skills 被写入 `.github/skills/` 目录供原生发现

**Skill 来源**：
- GitHub 仓库（主要来源）
- 本地定义
- Workspace 级别 vs 本地（"clarify local vs workspace skills to reduce user confusion" — v0.1.34 fix）

**已观察到的 skills**：
- `frontend-design` (anthropics/skills)
- `shadcn` (shadcn/ui)
- `ui-ux-pro-max`
- `web-design-guidelines` (vercel-labs/agent-skills)

### 4.3 信任模型

- SHA-256 computedHash 锁定版本
- 无签名验证机制
- 无权限隔离（skill 内容直接注入 prompt）
- 无 skill 运行时沙箱

---

## 5. Issue 任务系统

### 5.1 Issue 生命周期

```
backlog → todo → in_progress → in_review → done
                                         → cancelled
                                         → blocked (agent 报告)
```

**触发机制**:
- Issue 从 backlog 移出时自动触发 agent (#1006)
- Agent 被 assign 时触发
- 评论触发（包括已关闭 issue 的评论）
- Autopilot 定时/事件触发

### 5.2 Issue → Agent 分配

- `assignee` 可以是人或 agent（多态模型）
- Agent 通过 CLI 或 UI 被分配到 issue
- 一个 issue 可以有多个 agent 协作

### 5.3 Sub-issue 支持

- 父子 issue 关系（parent_issue_id）
- CLI: `multica issue update --parent <id>`
- UI: "Set parent issue" / "Add sub-issue" 菜单
- Sub-issue 进度可作为 card 属性显示

### 5.4 评论系统

- Agent 可以发表评论
- 评论触发 agent re-engage（即使 issue 已关闭）
- `@mention` 语法是 **action 而非文本引用**（v0.2.6 docs 明确警告）
- assignee 的 on_comment path 使用 reply id 而非 thread root（v0.2.6 fix）

---

## 6. Autopilot 系统

v0.2.0 引入的**调度自动化**功能。

### 6.1 概念

Autopilot = **定时或事件触发的自动化规则**，可以：
- 创建 issue（`create_issue` 模式）
- 分配 agent 执行已有 issue（`run_only` 模式）
- 调度 cron 触发器

### 6.2 CLI

```shell
multica autopilot create     # 创建自动化规则
multica autopilot list       # 列出规则
multica autopilot trigger    # 手动触发
multica autopilot schedule   # 配置定时计划
```

### 6.3 实现细节

- Autopilot 创建的 issue 自动订阅 creator
- 时间戳使用可读 UTC 格式
- 状态切换改为 toggle（非 pause/activate 按钮）
- workspace_id 解析修复（v0.2.5、v0.2.6 多次修复，说明此处 bug 较多）
- hand-off guards（v0.2.6: daemon trigger hand-off 防护）

---

## 7. 多租户与 Workspace

### 7.1 隔离模型

- **Workspace** 是顶层隔离单元
- 每个 workspace 有独立的 issues、agents、skills、projects、members
- API 通过 `X-Workspace-Slug` header 路由（v0.2.1 从 ID 迁移到 slug-first）
- 数据库层面，所有业务表都有 `workspace_id` 外键

### 7.2 安全

- Workspace membership 验证（v0.1.33: 补丁 subscription/upload 泄漏）
- Issue 级别的 workspace 绑定验证（v0.2.1: 4 个 daemon handler 补丁）
- S3 upload key 按 workspace 隔离（v0.1.33）
- Auth open redirect 修复（v0.2.6）
- Custom_env 仅 owner/admin 可见（v0.2.0）
- Desktop shell.openExternal 限制 http/https（v0.2.1）

### 7.3 URL 重构

v0.2.1 经历了 workspace URL 重构的**反复 revert**：
1. `feat: workspace URL refactor + slug-first API identity` (#1131)
2. Revert (#1137)
3. `feat: workspace URL refactor v2 + rollback-safe compat layer` (#1138)
4. Revert (#1139)
5. Reapply (#1141)

这反映了**多租户 URL 方案在已有系统上的迁移复杂性**。

---

## 8. 项目管理

### 8.1 Projects

- Workspace 内部的项目分组
- Issue 可以归属到 project
- CLI: `multica project create/list`
- Sub-issue 进度可作为 project card 属性
- 计划中: Agent Team 绑定到 project（#1173）

### 8.2 搜索

- Cmd+K 全局搜索面板
- 支持: theme toggle, new issue/project, copy link, switch workspace
- Recent list 自动包含新建 issue

---

## 9. 实时通信

- **WebSocket** (gorilla/websocket) 双向通信
- WS events 触发 React Query cache invalidation
- **Ping/Pong 心跳**检测死连接（v0.1.35）
- Timeline 条目在 WS append 后重新排序

---

## 10. 部署与自托管

### 10.1 Docker Compose 自托管

```shell
make selfhost  # 启动 PostgreSQL + Go server + Next.js
```

- 默认开发 master code: `888888`（v0.2.6 默认禁用）
- `APP_ENV` 传入 backend container
- 本地上传持久化（Docker volume）
- `restart: unless-stopped` 策略

### 10.2 开发环境

- 共享 PostgreSQL 实例 + worktree 隔离（每个 worktree 独立数据库）
- `make dev` 自动设置
- 每个 worktree 的独立 CLI profile
- 全栈隔离测试

---

## 11. 代码质量与开发节奏

### 11.1 发布频率

| 版本范围 | 数量 | 时间跨度 | 日均 |
|---------|------|---------|------|
| v0.2.0-v0.2.6 | 7 releases | ~5 天 | 1.4/天 |
| v0.1.33-v0.1.35 | 3 releases | ~2 天 | 1.5/天 |

**极高频发布**，每天 1-2 个版本，说明处于快速迭代期。

### 11.2 代码语言分布

- TypeScript: 53.4%
- Go: 43.0%
- 其余: SQL, Shell, Docker 等

### 11.3 PR 特征

- 892 closed PRs / 119 open PRs (截至观察日)
- 大量 `agent/j/xxxx` 分支 — **AI agent 自己提交的 PR**
- commit 消息格式规范: `feat|fix|refactor|test|chore(scope): description`
- 有专门的 regression test 要求

### 11.4 测试实践

- Go: handler/trigger/usage/workspace/search 级别测试
- 前端: ContentEditor test, CLI client context headers test
- Daemon: cross-workspace regression test, codex subagent threadId filter test
- CI: lint + typecheck + test (前端), make test (Go)

---

## 12. 技术债务与已知问题

| 领域 | 问题 | 证据 |
|------|------|------|
| Autopilot | workspace_id 解析反复修复 | #1224, #1249, #1294 三次修 |
| URL 迁移 | 3次 revert 才稳定 | #1131→#1137→#1138→#1139→#1141 |
| Daemon 身份 | hostname 归一化问题 | #1070 提交后又 revert (#1207) |
| Desktop | 多次 electron-builder 发布类型修复 | #1242, #1268 |
| Editor | bubble menu 位置问题反复修复 | 4+ commits across v0.1.33-v0.2.0 |
| 安全 | 多个 workspace 隔离漏洞 | #1121, #1145, #935, #936 |
| self-hosting | 多个 env var 和配置问题 | #1061, #1063, #1307 |
