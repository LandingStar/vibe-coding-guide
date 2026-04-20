# Multica 架构研究报告

> 分析日期: 2026-04-20
> 来源: https://github.com/multica-ai/multica (v0.2.6, 16.7k stars)
> 目的: 评估多 agent 协调平台架构模式对本项目的借鉴价值

## 1. 项目定位

Multica 自称"open-source managed agents platform"，核心理念是将 coding agent 视为"真正的队友"：

- Agent 可被分配 issue、创建 issue、发表评论、更新状态
- 支持 Claude Code、Codex、OpenClaw、OpenCode、Hermes、Gemini、Pi、Cursor Agent 等多种 runtime
- 定位是 2-10 人 AI-native 团队的任务管理平台（"like Linear, but with AI agents"）

## 2. 技术架构

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Next.js    │────>│  Go Backend  │────>│   PostgreSQL     │
│   Frontend   │<────│  (Chi + WS)  │<────│   (pgvector)     │
└──────────────┘     └──────┬───────┘     └──────────────────┘
                            │
                     ┌──────┴───────┐
                     │ Agent Daemon │  本地执行
                     └──────────────┘
```

- **前端**: Next.js 16 (App Router) + Electron 桌面端 + monorepo (pnpm + Turborepo)
- **后端**: Go (Chi router, sqlc, gorilla/websocket)
- **数据库**: PostgreSQL 17 + pgvector
- **Agent 运行时**: 本地 daemon 检测可用 CLI 工具并执行任务
- **多租户**: workspace 隔离，`X-Workspace-ID` header 路由
- **实时通信**: WebSocket，WS events invalidate React Query cache

### 关键架构决策

1. **Internal Packages 模式**: 共享包导出原始 `.ts/.tsx`，由消费方 bundler 编译（零配置 HMR）
2. **严格包边界**: `core/`(零 DOM) → `ui/`(零业务逻辑) → `views/`(零框架依赖) → `apps/`(框架特定)
3. **状态管理分离**: React Query 管理 server state, Zustand 管理 client state, 严禁混用
4. **Platform Bridge**: `CoreProvider` 初始化 API client/auth/WS，每个 app 提供自己的 `NavigationAdapter`

## 3. Skills 系统

Multica 的 Skills 是"可复用知识单元"，核心理念是 **"every solution becomes a reusable skill for the whole team"**。

### 实现方式

- `skills-lock.json` 记录已安装 skills（name + source + sourceType + computedHash）
- Skills 来源是 GitHub 仓库（如 `anthropics/skills`, `shadcn/ui`, `vercel-labs/agent-skills`）
- Skills 通过 hash 锁定版本（类似 package-lock.json 模式）
- 当前看到的 skills 主要是 UI/UX 相关（frontend-design, shadcn, ui-ux-pro-max, web-design-guidelines）

### 与本项目 Pack 系统对比

| 维度 | Multica Skills | 本项目 Pack |
|------|---------------|------------|
| 存储 | GitHub 仓库 + skills-lock.json | 文件系统（本地 JSON） |
| 安装 | 远程拉取 + hash 锁定 | 本地放置 / site-packages |
| 作用域 | 项目级 | platform-default / official-instance / user-global / project-local 四级 |
| 合并 | 单一应用 | 优先级驱动合并链 |
| 内容 | 面向特定技术栈的知识 | 规则/约束/工具权限/文档类型/意图分类 |
| 治理 | 无 | constraint checking / gate resolution / override policy |

## 4. Agent 任务生命周期

Multica 的 agent 任务管理是其核心差异化能力：

1. **任务分配**: Issue → assign to agent（与分配给人一样）
2. **自动执行**: daemon 监听任务队列 → claim → start → 执行 → complete/fail
3. **进度流**: WebSocket 实时推送进度
4. **阻塞报告**: agent 主动报告 blockers
5. **评论互动**: agent 可以发表评论、创建新 issue

### Daemon 架构

- Go 编写的本地 daemon，后台运行
- 自动检测 PATH 上的 agent CLI（claude, codex 等）
- Runtime = 计算环境（本地或云端），向 server 报告可用能力
- 支持 concurrent task 执行 + stuck task 防护
- per-agent MCP config 支持

## 5. 借鉴价值评估

### 高价值借鉴点

1. **Skills 的 hash 锁定模式** → 本项目的 pack 版本管理目前较弱。可以考虑为 user-global pack 引入 `pack-lock.json` 式的 integrity check，防止意外修改
2. **严格包边界规则** → Multica 的 `core/` / `ui/` / `views/` 分层约束与我们的 pack 四级优先级思想相似，都是通过硬规则防止层级逆转
3. **Platform Bridge 模式** → `CoreProvider` + `NavigationAdapter` 的跨平台桥接方式，可参考用于 CLI / MCP / VS Code Extension 三入口面的统一初始化

### 中等价值借鉴点

4. **Agent 作为 assignee 的多态模型** → `assignee_type + assignee_id` 的设计可参考用于子 agent 的委派追踪
5. **"Compound skills over time"** 理念 → 我们的 user-global pack 已经部分实现了这个理念（成功的规则组合跨项目复用），未来可以增加自动提炼能力
6. **Workspace 隔离 + 切换** → Multica 的 workspace isolation 模式与我们的 project-local / user-global 两层隔离有相似性

### 低价值 / 不适用

7. **中心化 server 架构** — 本项目坚持文件系统分布式，不依赖 PostgreSQL
8. **React Query / Zustand 状态管理** — 前端技术选型差异，本项目 Extension 是轻量 VS Code webview
9. **daemon 长驻进程模型** — 本项目通过 MCP stdio 按需启动，无需 daemon

## 6. 与现有研究参考的关系

| 已有研究 | 关注维度 | Multica 补充维度 |
|---------|---------|-----------------|
| Claude Managed Agents | Skills 渐进加载 + 权限分层 + 上下文隔离 | 团队协作 + 任务分配 + runtime 调度 |
| OpenHands | pack 载入 + 上下文层次 | hash 锁定 + skills-lock.json |
| LangGraph/CrewAI | 多 agent 编排 | 产品化的 agent-as-teammate 体验 |

## 7. 行动建议

| 优先级 | 建议 | 依据 |
|--------|------|------|
| 可考虑 | 为 user-global pack 引入 integrity hash | Multica skills-lock.json 的 computedHash |
| 可考虑 | Pack install/publish CLI 命令（从 GitHub 仓库安装 pack） | Multica skills 的 GitHub source 模式 |
| 长期 | 子 agent 委派的多态追踪模型 | Multica 的 assignee_type + assignee_id |
| 不建议 | 引入中心化 server / daemon | 与项目文件系统分布式定位冲突 |

## 8. 结论

Multica 的核心创新在于**将 AI agent 作为一等公民融入团队协作流程**（issue 分配、评论、状态更新）。其技术架构是标准的 SaaS monorepo 模式，无特别新颖之处。

对本项目最有借鉴价值的是：
1. Skills 的 **hash 锁定 + 远程来源** 模式 — 可用于 pack 版本管理
2. **"compound skills over time"** 理念的产品化实现 — 我们的 user-global pack 已经是初步形态，未来可增加自动提炼
3. **严格层级边界的工程实践** — 作为架构治理的正面案例
