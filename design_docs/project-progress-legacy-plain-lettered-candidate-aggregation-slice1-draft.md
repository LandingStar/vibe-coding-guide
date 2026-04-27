# Slice 1 Draft — Project Progress Legacy Plain Lettered Candidate Aggregation

## Contract focus

本 Slice 只固定 `direction-candidates-after-phase-35.md` 中 plain `### A./B./C.` 历史候选块的最小 projection contract。

## Section selection boundary

只命中以下 section：

1. `##` heading 标题不含 `project progress`
2. section 内存在 plain `### A./B./C.` candidate block
3. candidate block 内存在 `做什么` / `依据` / `当前判断` 等现有 lettered parser 已消费的字段

## Candidate node shape

1. graph id 继续复用 `direction-candidates-global`
2. candidate node id 继续使用 `section:{index}:candidate:{letter}`
3. candidate title 继续使用 `{letter}. {title}`
4. candidate kind 保持 `decision`
5. recommended surface 继续使用 candidate-local `当前判断`

## Out of scope

1. companion prose projection
2. plain lettered 之外的 heading 变体归一化
3. based on chronology 的 latest section 重算