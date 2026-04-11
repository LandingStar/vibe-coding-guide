# Session Handoff Standard

## 文档定位

本文件定义 `{{PROJECT_NAME}}` 在多会话切换时使用的标准 handoff 规则。

## 适用范围

本标准适用于：

- 当前切片已经到达安全停点
- 需要把工作转交给下一次会话
- 需要把边界、验证与下一步合同显式写下来

本标准不服务于任意中途暂停的随手总结。

## 权威优先级

handoff 不是最高真相来源。

若 handoff 与其他信息冲突，优先级应为：

1. 用户在最新对话中的明确决定
2. 当前 workspace 的现实状态
3. 正式设计文档与协议文档
4. 当前 active handoff

## 安全停点

只有当以下条件同时成立时，才应生成正式 handoff：

- 当前范围可以用一句话说清
- 已完成项与未完成项可以稳定分开
- 接手方不依赖当前对话的隐性记忆也能继续

当且仅当满足安全停点时：

- model 可以主动发起 handoff 构建
- handoff 分支中只有 `blocked` 是停止信号
- 若结果不是 `blocked`，model 可以继续执行下一条直接相关的 handoff 指令

safe-stop close 不只包含 handoff 本身，还应包含一组 writeback bundle：

- canonical handoff generation
- `CURRENT.md` refresh
- Checklist / Phase Map / 当前方向候选文档 / checkpoint 同步

同时还要按实际情况判断条件项，例如是否清除 active planning-gate 标记、是否 supersede 旧 active canonical handoff、是否同步协议文档。

## Core Fields

每个 handoff 默认至少应包含：

- `Summary`
- `Boundary`
- `Authoritative Sources`
- `Verification Snapshot`
- `Open Items`
- `Next Step Contract`
- `Intake Checklist`

若 handoff 涉及需要 review 的 artifact（如设计结论、phase-close proposal），应在 `Open Items` 或 `Next Step Contract` 中注明该 artifact 在 review state machine 中的当前状态（`proposed` / `waiting_review` / `approved` / `rejected` / `revised` / `applied`）。

## 接手流程

接手方默认按以下顺序恢复上下文：

1. 读 `.codex/handoffs/CURRENT.md`
2. 重读其中列出的正式文档
3. 核对 workspace 现实状态
4. 再决定是否继续当前合同

若 intake 结果为 `blocked`，必须停止并显式暴露阻断原因；若结果不是 `blocked`，model 可以继续执行当前合同。

## 禁止事项

handoff 中禁止：

- 复制正式文档的大段正文
- 用 handoff 代替阶段文档或状态板
- 把未验证结论写成既成事实
- 在边界未收口时硬生成 handoff
