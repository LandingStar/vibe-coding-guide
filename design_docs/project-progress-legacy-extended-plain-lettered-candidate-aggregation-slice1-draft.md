# Slice 1 Draft — Project Progress Legacy Extended Plain Lettered Candidate Aggregation

## Contract focus

本 Slice 只固定 `direction-candidates-after-phase-35.md` 中无前缀 extended plain lettered headings 的最小 projection contract。

## Section selection boundary

只命中以下 section：

1. `##` heading 标题不含 `project progress`
2. section 内存在无前缀 extended plain lettered candidate block
3. candidate block 内继续使用现有 `做什么` / `依据` / `当前判断` 字段

## Candidate node shape

1. graph id 继续复用 `direction-candidates-global`
2. candidate node id 继续使用 `section:{index}:candidate:{letter}`
3. candidate title 继续使用 `{letter}. {title}`
4. candidate kind 保持 `decision`
5. recommended surface 继续使用 candidate-local `当前判断`

## Out of scope

1. companion prose projection
2. recency semantics
3. 非字母 heading 的额外变体归一化