# Session Handoff Standard

## 1. 文档定位

本文件定义本项目在多会话切换时使用的标准交接协议。

它解决的问题是：

- 何时应生成正式 handoff
- handoff 应包含哪些固定信息
- 接手方应如何恢复上下文
- 如何避免把 handoff 变成第二套状态板或第二套设计文档

本文件是 handoff 协议的 authoritative source。

skill、脚本、模板与校验工具都只能实现本文件，不得重新定义本文件。

---

## 2. 适用范围

本标准适用于本项目中需要跨会话转移上下文的场景，尤其包括：

- 某个大阶段已经完成并准备切回 planning-gate
- 某个小 phase 已满足完成定义，且当前是安全停点
- 需要把当前工作可靠移交给后续会话或其他协作者

本标准默认不服务于“任意中途暂停”的随手总结。

第一版仅支持以下 handoff 类型：

- `stage-close`
- `phase-close`

当前不支持：

- `interrupt`
- `partial-progress`
- 未达到安全停点的中断性交接

---

## 3. 权威来源与优先级

handoff 不是最高真相来源。

若 handoff 与其他信息冲突，优先级为：

1. 用户在最新对话中的明确决定
2. 当前 workspace 的现实状态
3. 项目正式文档与协议文档
4. 当前 active handoff
5. 历史 handoff

其中：

- `design docs/Project Master Checklist.md` 是总入口与状态板
- `design docs/Global Phase Map and Current Position.md` 是当前阶段口径入口
- 当前 handoff 只负责记录“本次交接边界内的增量事实与接手约束”

handoff 不得复制上述文档的大段正文来代替引用。

---

## 4. Handoff 类型与安全停点

### 4.1 `stage-close`

适用于某个大阶段或连续建设块已经完成，并且可以回到 planning-gate 的情况。

它必须满足：

- 当前阶段边界已经明确收口
- 为什么可以在这里停下已有清晰说明
- 下一阶段应回到哪个 planning-gate 位置已有明确指向

### 4.2 `phase-close`

适用于某个小 phase 已满足完成定义，但所属大阶段未必完全结束的情况。

它必须满足：

- 当前 phase 的完成边界明确
- 当前对话停在已收口的 phase 边界，而不是半完成状态
- 下一会话可从清晰的下一小步继续

### 4.3 安全停点原则

只有当以下条件成立时，才应生成正式 handoff：

- 当前范围边界可以用一句话说清
- 已完成项与未完成项可以稳定分开
- 接手方无需依赖当前会话的隐性上下文才能继续

若做不到以上三点，则不应生成正式 handoff。

### 4.4 Model 执行语义

当且仅当当前状态已经满足安全停点时：

- model 可以主动发起 handoff 构建，不需要额外等待显式 slash 指令。
- 这种主动发起只适用于 handoff 协议允许的正式收口场景，不适用于中断态或半完成态。
- 主动发起不改变 handoff 的前置条件；`kind`、`scope_key`、authoritative refs 与结构校验仍必须明确可判定。

### 4.5 Safe-Stop Writeback Bundle

安全停点下，handoff 的生成与轮转只是 safe-stop close 的一部分，不是全部。

当一次 safe-stop 需要被正式收口时，默认 writeback bundle 至少应覆盖：

- canonical handoff generation
- `CURRENT.md` refresh
- `Project Master Checklist` 同步
- `Global Phase Map` 同步
- 当前方向候选文档同步
- checkpoint 同步

同时应显式区分条件项，例如：

- 是否需要清除 active planning-gate 标记
- 是否需要 supersede 旧 active canonical handoff
- 是否需要回写 handoff / workflow 协议文本

safe-stop helper、checkpoint 与 authority docs 若需要记录“当前 safe stop 由哪份 canonical handoff 关闭”，应共用同一份最小 pointer footprint，而不是复制 handoff 正文。

该 footprint 第一版只允许包含：

- `handoff_id`
- `source_path`
- `scope_key`
- `created_at`

因此，“handoff 已生成”并不自动等于“safe-stop close 已完成”；只有当该 bundle 的必做项与命中的条件项都已处理后，当前 safe-stop 才算真正完成。

---

## 5. 目录结构与生命周期

handoff 文件统一存放在：

- `.codex/handoffs/history/`
- `.codex/handoffs/CURRENT.md`

规则如下：

- `history/*.md` 是 canonical handoff
- `CURRENT.md` 是当前 active handoff 的镜像入口
- 历史 handoff 默认保留，但一般情况下不作为默认读取对象
- 新会话默认只读 `CURRENT.md`
- 只有在冲突、追溯或审查时才读取历史 handoff
- handoff 分支中的后续步骤可以由 model 连续执行，但只有在前一步未返回 `blocked` 时才允许继续

在首次 canonical handoff 生成之前，`CURRENT.md` 可以暂时保留 bootstrap placeholder。

该 placeholder：

- 不是正式 handoff
- 不参与 `draft / active / superseded` 生命周期
- 只用于固定入口位置与提醒后续刷新方式

handoff 生命周期状态为：

- `draft`
- `active`
- `superseded`

同一时刻应只有一个 `active` canonical handoff 被 `CURRENT.md` 镜像。

---

## 6. Core Fields

每个 handoff 必须包含以下 core fields。

### 6.1 Metadata

必须包含：

- `handoff_id`
- `entry_role`
- `kind`
- `status`
- `scope_key`
- `safe_stop_kind`
- `created_at`
- `supersedes`
- `authoritative_refs`
- `conditional_blocks`
- `other_count`

### 6.2 Boundary

必须明确：

- 本次交接完成到哪里
- 为什么这是安全停点
- 哪些内容明确不在本次完成范围内

### 6.3 Authoritative Sources

必须列出接手方最低限度必须重读的正式文档。

要求：

- 只列必须读的入口
- 以引用为主，不复制正文
- 数量应保持克制

### 6.4 Session Delta

必须只写本轮相对上一个稳定状态的增量，包括：

- 新增内容
- 修改内容
- 本轮形成的新约束或新结论

不得把项目总历史重新抄写一遍。

### 6.5 Verification Snapshot

必须明确：

- 跑了哪些自动化
- 做了哪些手测
- 哪些验证未做
- 哪些结论仍未验证

### 6.6 Open Items

必须明确：

- 当前未决项
- 已知风险
- 不能默认成立的假设

### 6.7 Next Step Contract

必须明确：

- 下一会话建议只推进哪条窄主线
- 下一会话明确不做什么
- 为什么当前应在这里停下

### 6.8 Intake Checklist

必须明确接手方应做的最小核验动作，用于防止把 handoff 当作真相本身。

---

## 7. 通用正文章节顺序

每个 handoff 正文默认按以下顺序组织：

1. `Summary`
2. `Boundary`
3. `Authoritative Sources`
4. `Session Delta`
5. `Verification Snapshot`
6. `Open Items`
7. `Next Step Contract`
8. `Intake Checklist`
9. `Conditional Blocks`
10. `Other`

除本文件明确允许的额外章节外，不应随意改动顺序。

---

## 8. `stage-close` 额外要求

`stage-close` 除通用要求外，还必须包含：

- `Why This Stage Can Close`
- `Planning-Gate Return`

其中必须回答：

- 为什么当前大阶段到这里可以结束
- 下一次应回到哪个 planning-gate 位置
- 下一阶段候选主线是什么
- 下一阶段明确不做什么

`stage-close` 应能支持用户判断：“当前是否真的适合在这里收口”。

---

## 9. `phase-close` 额外要求

`phase-close` 除通用要求外，还必须包含：

- `Phase Completion Check`
- `Parent Stage Status`

其中必须回答：

- 当前小 phase 的完成定义是否满足
- 所属大阶段是继续中、接近尾声，还是已建议收口
- 下一步是继续同一大阶段内的哪条窄主线

---

## 10. 生成流程

生成 handoff 时，必须按以下顺序执行：

1. 确认当前是否处于安全停点
2. 确定 handoff 类型为 `stage-close` 或 `phase-close`
3. 填写 core fields
4. 匹配并展开所有命中的 conditional blocks
5. 填写正文固定章节
6. 仅在确有必要时填写 `Other`
7. 对 `Other` 做归类反查
8. 通过结构校验后，才允许进入 active 轮转流程

补充规则：

- 若 handoff 生成结果未返回 `blocked`，model 可以继续进入与当前目标直接相关的下一步 handoff 指令。
- 若当前目标包含刷新 active mirror，则可继续执行 `refresh current`；不需要把“继续轮转”再退回成额外的显式 slash 前置。
- 若任一步返回 `blocked`，必须停止自动推进并显式暴露阻断原因。

若第 1 步失败，则本轮不应生成正式 handoff。

---

## 11. 接手流程

接手方默认按以下顺序恢复上下文：

1. 读取 `.codex/handoffs/CURRENT.md`
2. 重读其中列出的 `authoritative_refs`
3. 执行 `Intake Checklist`
4. 核对当前 workspace 的现实状态
5. 只在必要时追读历史 handoff
6. 若发现 handoff 与现实状态冲突，以现实状态和正式文档为准
7. 再决定是否继续执行 `Next Step Contract`

接手方不得仅凭 handoff 正文直接继续编码，而跳过最小核验。

补充规则：

- `accept` 结果若为 `blocked`，必须停止并转入阻断处理。
- `accept` 结果若为 `ready` 或 `ready-with-warnings`，model 可以继续执行当前任务所需的下一步，而不需要因为“不是显式 slash 调用”而停下。

---

## 12. `Other` 准入与审查规则

`Other` 是受控逃生口，不是杂项收纳区。

只有当某条信息同时满足以下条件时，才允许进入 `Other`：

- 现有 core fields 无法准确承载
- 已命中的 conditional blocks 也无法准确承载
- 该信息对下一会话有实际影响

每条 `Other` 必须包含：

- `Title`
- `Why not fit existing fields`
- `Impact on next session`
- `Verification status`
- `Source refs`
- `Content`

约束：

- 没有 `Why not fit existing fields` 的条目无效
- 若内容可归入现有字段，则必须回填，不能留在 `Other`
- `Other` 默认应极少使用
- 若同类 `Other` 重复出现，应考虑晋升为正式 conditional block

---

## 13. 禁止事项

handoff 中禁止出现：

- 大段复制正式文档正文
- 原始长日志堆积
- 无结构的思维流
- 未验证却写成既成事实的判断
- 与当前交接边界无关的大型 backlog
- 用 `Other` 替代已有正式字段
- 在 handoff 中重新定义项目协议

---

## 14. 相关文档

- `design docs/Project Master Checklist.md`
- `design docs/Global Phase Map and Current Position.md`
- `design docs/Verification Gate and Phase Acceptance Workflow.md`
- `design docs/tooling/Session Handoff Conditional Blocks.md`
- `AGENTS.md`
