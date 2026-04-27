# 设计草案 — Orchestration Bridge Coordinator Glue Slice 1

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-coordinator-glue.md` 的 Slice 1 设计草案。

## 目标

当前只固定最小 coordinator step contract：

1. 输入是一条 `BridgeWorkItem`
2. 输入包含当前 `group_items` tuple 与目标 `group_item_id`
3. 输入包含该目标 group item 对应的 executor dict execution result
4. 输出返回 updated group item、updated group-item tuple、updated work item、stop decision

## 当前推荐

当前推荐 coordinator 只做三步：

1. 用 execution-result adapter 更新一个 group item
2. 对更新后的 group-item tuple 做 work-item roll-up
3. 基于 roll-up 结果调用 stop evaluator

## 当前不做的事

当前不做：

1. daemon queue / persistence
2. executor 主流程重构
3. landing artifact writeback

## 当前判断

我当前判断这条 slice 值得先落地，因为它能在不引入额外 runtime state 的前提下，直接验证 helper 链能否组成最小闭环。