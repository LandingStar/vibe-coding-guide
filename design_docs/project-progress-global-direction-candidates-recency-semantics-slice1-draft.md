# Slice 1 Draft — Project Progress Global Direction-Candidates Recency Semantics

## Contract focus

本 Slice 只固定 `direction-candidates-global` 中 numbered sections 的 latest/current 选择规则。

## Recency source-of-truth

1. 优先从 `##` section title 的日期前缀提取 recency key
2. 当日期相同或缺失时，使用更早的文档位置作为 tie-break
3. 只对当前 `status_mode == latest` 的 sections 参与 latest section 竞争

## Affected surface

1. section node status
2. numbered candidate status 继承的 latest section 归属
3. section metadata 中可选记录 recency key / latest selection reason

## Out of scope

1. lettered candidate 的推荐规则
2. companion prose
3. planning-gate / checklist / phase-map 之外的新 graph