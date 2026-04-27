# Project Progress Richer Candidate-Doc Linkage Slice 1 Draft

## 目标

让 `direction-analysis-current` / `direction-candidates-global` 中的 candidate nodes 不再只是孤立的候选条目，而能通过显式 doc ref 与 checklist / phase map / planning-gate 等 factual graphs 建立可见 linkage。

## 当前建议的 contract

1. 对 checklist / phase map / global direction-candidates 增加稳定的 `reference:source-document` 节点
2. 对 current/global candidate nodes 的 `basis_refs` 做最小翻译
3. 若 `basis_refs` 命中当前 graph source path，则连到对应 graph 的稳定 entry node
4. 若 `basis_refs` 命中 planning-gate path，则连到 `planning-gates-index` 中对应 node

## 当前建议的边界

1. 只用显式 doc ref，不做 title 相似度匹配
2. 只覆盖当前已有 factual/candidate graphs
3. 不引入新的 source projection

## 当前判断

这条 slice 足够窄，因为它只把现有 graph 之间已经存在于文档中的显式引用翻译成 linkage，不会把范围扩到新的 parser 或更宽的 semantic inference。