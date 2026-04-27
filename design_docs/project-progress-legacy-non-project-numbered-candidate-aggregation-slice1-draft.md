# Slice 1 Draft — Project Progress Legacy Non-Project Numbered Candidate Aggregation

## Contract focus

本 Slice 只固定 `direction-candidates-after-phase-35.md` 中 legacy non-project numbered sections 的最小 projection contract。

## Section selection boundary

只命中以下 section：

1. `##` heading 标题不含 `project progress`
2. section 内存在 `- 候选 1/2/3` 这类 numbered candidate block
3. section 内存在 `当前倾向`，可继续映射到 section-level recommended candidate surface

## Candidate node shape

1. graph id 继续复用 `direction-candidates-global`
2. candidate node id 继续使用 `section:{index}:candidate:{number}`
3. candidate title 继续使用 `候选 {number}. {title}`
4. candidate kind 保持 `decision`

## Out of scope

1. plain `### A./B./C.` headings
2. `当前 AI 倾向判断` sibling section 的额外解析
3. 基于日期或文档位置的 section recency 重算