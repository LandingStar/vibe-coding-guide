# Project Progress Research Compass Topic Projection Slice 1 Draft

## 目标

把 `review/research-compass.md` 的 `按问题检索` 主题入口补进 `research-compass-current` graph，使 graph 不只包含研究文档条目，还包含“按什么问题去读这些条目”的主题层。

## 当前建议的 contract

1. `按问题检索` 中每个 H3 topic 生成一个稳定 topic node
2. topic node 状态固定为 `completed`
3. topic node 通过 `reference` edge 指向该 topic 下列出的 research entry nodes
4. 第一版只消费 markdown doc refs，不引入新主题匹配规则

## 当前建议的边界

1. 不对 topic 做跨文档语义匹配
2. 不从自然语言句子里猜测额外 references
3. 不把 topic 直接映射为 cross-graph edge target

## 当前判断

这条 slice 足够窄，因为它只给现有 `research-compass-current` graph 增加一个显式 topic layer，不会把 scope 扩到新的 graph 类型或新的 linkage 机制。