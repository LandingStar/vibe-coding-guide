# Project Progress External Reference Projection Slice 1 Draft

## 目标

让 progress graph 不只展示内部状态面，还能把 `review/research-compass.md` 这类外部研究入口投影成独立 graph，并为当前 candidate `basis_refs` 提供稳定的 external-reference linkage target。

## 当前建议的 contract

1. 新增 `research-compass-current` graph
2. graph 至少包含 `reference:source-document` 节点
3. 第一版只投影 `## 全量研究地图` 中可稳定解析的研究条目
4. 每个研究条目节点以其 repo-relative markdown 路径作为稳定 node id
5. `basis_refs` 若命中 `review/research-compass.md` 或其稳定研究条目路径，应翻译成 explicit cross-graph linkage

## 当前建议的边界

1. 不做 `review/` 全量扫面或 topic graph 泛化
2. 不做 title similarity / tag similarity / embedding matching
3. 只覆盖 `research-compass.md` 中明确列出的稳定入口路径

## 当前判断

这条 slice 足够窄，因为它复用了现有 `basis_refs` 翻译机制，只额外补一张最小 external-reference graph 与少量稳定 target 节点，不会把范围扩到新的 consumer 或更宽的知识图谱。