# Project Progress Non-Project-Progress Candidate Aggregation Slice 1 Draft

## 目标

把 `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 且采用 `### 新候选 A/B/C` 候选块的 section 投影进现有 `direction-candidates-global` graph，让 multigraph 开始覆盖更广的非主线方向历史。

## 当前建议的 graph contract

1. graph id 继续复用：`direction-candidates-global`
2. source path：`design_docs/direction-candidates-after-phase-35.md`
3. section 节点：每个命中的非 `project progress` `##` section 生成一个 `milestone` 节点
4. candidate 节点：按 `### 新候选 A/B/C` 生成，kind 先统一为 `decision`

## 当前建议的 selection boundary

1. 只选标题不含 `project progress` 的 `##` section
2. 只选 section 内存在 `### 新候选 A/B/C` 的 block
3. 当前忽略 `用户选定下一步`、`因此当前实际下一条 planning-gate 已切换为`、`当前更窄的入口是` 等 companion prose
4. 当前不解析纯 `### A./B./C.`、`### D./E./F.` 的旧格式 backlog section

## 当前建议的 recommended surface

1. 若 candidate block 中出现 `当前判断：**推荐**`，则该 candidate 标记为 recommended
2. recommended candidate 先用 `in_progress` 表示
3. 其余 candidate 先统一为 `pending`

## 当前判断

这条 slice 足够窄，因为它只新增一种稳定的非 `project progress` 候选块格式，不会一开始就把整篇 backlog 的所有候选表达形式都卷进来。