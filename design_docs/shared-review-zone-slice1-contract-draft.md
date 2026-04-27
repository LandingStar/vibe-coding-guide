# 设计草案 — Shared-Review Zone Slice 1 Contract And Preflight

本文是 `design_docs/stages/planning-gate/2026-04-24-shared-review-zone-contract-and-preflight.md` 的 Slice 1 设计草案。

## 目标

当前目标不是让多个 child 自动合并重叠修改，而是引入一条**显式、默认收紧、可审计**的 overlap 例外路径：

1. 默认规则保持不变：`allowed_artifacts` overlap 仍被 preflight 拒绝
2. 只有 child 明确声明同一个 shared-review zone 时，overlap 才允许通过 preflight
3. 一旦通过该例外路径，terminal review 倾向必须收敛到 `review_required`

## 设计原则

1. 不重写现有 `Subagent Contract` / `Subagent Report` 主 schema 家族
2. 优先把 zone 语义放在现有 companion objects 与 `parallel_children` hints 上
3. zone 只授予“进入 grouped review 的资格”，不授予自动 merge 权限
4. Slice 1 先锁定同一 artifact 的 shared review，不扩到 patch-level 或 section-level merge

## 推荐的最小字段集合

### 1. ParallelChildTask

推荐新增：

- `shared_review_zone_id: str = ""`

用途：

- 表达 child 是否被 parent 显式放入某个 shared-review zone
- 空字符串表示该 child 仍受严格 disjoint write set 规则约束

当前不推荐在 `ParallelChildTask` 上同时引入更多 zone policy 字段，因为 Slice 1 只需要识别“是否属于同一显式 zone”。

### 2. preflight result surface

当前 `preflight_subgraph_task_group()` 返回：

- `valid`
- `errors`
- `normalized_boundaries`

推荐最小扩展为：

- `overlap_decisions`

每个 decision 最小包含：

- `left_child_id`
- `right_child_id`
- `left_path`
- `right_path`
- `decision`
  - `blocked_overlap`
  - `shared_review_zone_allowed`
- `shared_review_zone_id`
- `reason`

这样做的意义是：

1. preflight 不再只有“报错字符串”一种输出
2. grouped review / audit / tests 后续都能复用同一份机器可读证据

### 3. grouped review marking surface

当前 `GroupedReviewOutcome` 只有：

- `outcome`
- `child_reviews`
- `changed_artifacts`
- `unresolved_items`
- `assumptions`
- `blocked_reason`

Slice 1 不建议直接改 `GroupedReviewOutcome` dataclass。

更窄的做法是：

1. 先让 preflight 产出 machine-readable `overlap_decisions`
2. Slice 2 再决定是否需要把 `review_driver` / `shared_review_zone_id` 正式提升到 grouped review companion object

原因：

- 当前 Slice 1 的核心是 contract/preflight，不是 grouped review surface 的最终定稿

## 推荐的 preflight 规则

### 1. 默认规则不变

若两个 child 的 normalized `allowed_artifacts` overlap，且二者都没有相同的 `shared_review_zone_id`，则：

- preflight `valid = False`
- 写入 `blocked_overlap` decision
- 保持当前错误面兼容

### 2. zone 例外只在显式同 zone 时成立

若 overlap child 满足：

1. `shared_review_zone_id` 非空
2. 左右 child 的 zone id 完全相同

则：

- preflight 不因这组 overlap 直接失败
- 记录 `shared_review_zone_allowed` decision

### 3. Slice 1 推荐只覆盖 same-artifact shared review

为了避免 scope 失控，Slice 1 推荐附加一个更窄约束：

- zone 例外只覆盖**同一规范化 artifact path**
- 不覆盖目录级 ancestry overlap，例如 `docs` 与 `docs/a.md`

原因：

1. 当前 path overlap 逻辑把 ancestry 也视为 overlap
2. 如果目录级 overlap 也一并放开，shared-review zone 会瞬间变成大范围共享写权限
3. same-artifact shared review 足够验证这条例外路径是否值得保留

## 推荐的 parent-built child batch hints 形态

在当前 `parallel_children` entry 上，推荐最小追加：

- `shared_review_zone_id`

示意：

```json
{
  "contract": {"contract_id": "contract-a", "mode": "subgraph"},
  "shared_review_zone_id": "zone-docs-a"
}
```

这样做的理由：

1. parent 是唯一可以授权 overlap 例外的一方
2. 当前 `parallel_children` 已经是 parent-built child batch 的入口，不需要再开第二套输入通道

## 当前不做的设计

Slice 1 明确不做：

1. patch-level / section-level conflict expression
2. grouped review apply 之后的 merge algorithm
3. zone 内 child 的 handoff / escalation 规则
4. 目录级 shared-review zone

## 当前推荐

我当前推荐：

1. 先给 `ParallelChildTask` 增加单一字段 `shared_review_zone_id`
2. 让 `parallel_children` hints 成为该字段的唯一输入入口
3. 扩展 preflight 返回 `overlap_decisions`
4. Slice 1 仅支持 same-artifact shared review

这条路线最小、最稳，也最容易被现有 executor / tests / audit surface 吸收。