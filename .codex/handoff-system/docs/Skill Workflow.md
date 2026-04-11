# Project Handoff Skill Workflow

## 1. 文档定位

本文件描述项目专用 handoff skill 未来应支持的工作流。

它的目标是固定：

- `generate handoff`
- `accept handoff`
- `refresh current`
- `rebuild handoff`

四类流程的项目内实现边界。

本文件不定义 handoff 协议本身，只定义项目内 skill 应如何执行该协议。

---

## 2. 支持的工作流

项目专用 handoff skill 未来默认支持以下工作流：

- `generate handoff`
- `accept handoff`
- `refresh current`
- `rebuild handoff`

当前已实现的只有：

- `generate handoff`
- `accept handoff`
- `refresh current`
- `rebuild handoff`

其中：

- `generate handoff` 负责在安全停点生成新的 canonical handoff
- `accept handoff` 负责在新会话中按固定流程恢复上下文
- `refresh current` 负责把最新 active canonical handoff 镜像到 `CURRENT.md`
- `rebuild handoff` 负责在 blocked intake 后重建 replacement canonical draft

---

## 3. `generate handoff` 流程

推荐按以下顺序执行：

1. 判断当前是否属于 `stage-close` 或 `phase-close`
2. 确认当前是否真的是安全停点
3. 读取 handoff 协议文档
4. 收集本轮 authoritative refs、增量事实与验证结果
5. 判定命中的 conditional blocks
6. 填写 canonical handoff 模板
7. 对 `Other` 做归类反查
8. 通过结构校验后，写入 `.codex/handoffs/history/`
9. 若生成结果未返回 `blocked` 且当前目标需要 active mirror，model 可以继续通过 `refresh current` 刷新 `.codex/handoffs/CURRENT.md`

当前明确不允许：

- 在未收口的中断状态下强行生成正式 handoff
- 先写 `CURRENT.md`，再回头补 canonical handoff
- 把本应进入现有字段的内容塞进 `Other`

补充执行语义：

- 安全停点下，`generate handoff` 可以由 model 主动调用，不需要显式 slash 才能进入。
- 但主动调用不等于放宽前置条件；safe stop、kind、scope 与结构校验仍必须成立。
- 只有 `blocked` 才是停止信号；若未 `blocked`，model 可以继续执行 handoff 分支中的下一步。

当前实现位置：

- `.codex/handoff-system/skill/project-handoff-generate/`
- `.codex/handoff-system/skill/project-handoff-refresh-current/`

---

## 4. `accept handoff` 流程

推荐按以下顺序执行：

1. 读取 `.codex/handoffs/CURRENT.md`
2. 判断它是否仍是 bootstrap placeholder
3. 读取其中列出的 `authoritative_refs`
4. 逐项执行 `Intake Checklist`
5. 核对当前 workspace 的现实状态
6. 检查 `conditional_blocks` 是否与当前任务相关
7. 对 `Other` 做严格复核
8. 只有在最小核验完成后，才开始继续下一步工作

当前明确不允许：

- 只看 `Summary` 就继续实现
- 跳过 `authoritative_refs`
- 把 `Other` 直接当成已验证事实

当前 proto-skill 版本改为：

1. 支持显式 `CURRENT.md` 入口或显式 handoff 路径
2. 先验证入口是否能解析到 canonical handoff
3. 再检查结构、refs 与最小 workspace reality
4. 输出 `ready / ready-with-warnings / blocked`

补充执行语义：

- `blocked` 必须停止并上抛。
- `ready` / `ready-with-warnings` 不要求额外的显式 slash 才能继续当前任务。

当前 accept 端仍不内联实现：

- blocked 后 rebuild

其中 blocked 后 rebuild 现已由独立 `rebuild handoff` skill 承担，而不是内联到 `accept`。

---

## 5. `refresh current` 流程

`CURRENT.md` 的职责只是：

- 提供稳定入口
- 镜像当前 active canonical handoff

推荐流程为：

1. 选定新的 active canonical handoff
2. 检查其状态是否已从 `draft` 升到 `active`
3. 将旧 active handoff 标记为 `superseded`
4. 用新的 canonical 内容刷新 `CURRENT.md`
5. 记录 `source_handoff_id`、`source_path` 与必要的结构摘要

补充执行语义：

- `refresh current` 可以作为 `generate handoff` 成功后的连续下一步由 model 主动执行。
- 只有在校验或轮转结果返回 `blocked` 时，才应停止 handoff 分支自动推进。

`CURRENT.md` 不应被手工写成独立事实源。

当前该流程已实现到项目专用 skill 中：

- `.codex/handoff-system/skill/project-handoff-refresh-current/`

---

## 6. `rebuild handoff` 流程

`rebuild handoff` 的职责是：

- 在 intake `blocked` 后生成 failure report
- 保留失败 source handoff
- 重建新的 canonical `draft`

推荐流程为：

1. 从 `CURRENT.md` 或显式 handoff path 重跑 intake
2. 区分 `invalid-handoff` 与 `reality-mismatch`
3. 将失败原因写入 `.codex/handoffs/reports/`
4. 从 surviving metadata、authoritative refs 与当前 workspace reality 重建新 draft
5. 保持原失败 handoff 不变
6. 若重建结果未返回 `blocked` 且当前目标需要重新成为 current，可继续走 `refresh current`

当前该流程已实现到项目专用 skill 中：

- `.codex/handoff-system/skill/project-handoff-rebuild/`

---

## 7. 失败与回滚策略

若任一步失败，项目专用 skill 应优先保守处理：

- 若结构校验失败，不生成 active handoff
- 若 `Other` 审查失败，不刷新 `CURRENT.md`
- 若 canonical handoff 未通过校验，不允许覆盖既有 active mirror

推荐保留：

- 原有 active handoff
- 失败原因
- 待修复项

而不是留下半有效的 `CURRENT.md`。

---

## 8. 当前边界

本文件当前只定义：

- 未来 skill 的工作流
- 项目内 generate / accept / refresh current / rebuild handoff 的顺序
- 出错时的保守处理原则

本文件当前不定义：

- 具体命令行接口
- prompt 形态
- 脚本参数
- 自动模板渲染实现

这些内容应在后续真正实现项目专用 skill 时，再放入：

- `.codex/handoff-system/skill/`
- `.codex/handoff-system/scripts/`
