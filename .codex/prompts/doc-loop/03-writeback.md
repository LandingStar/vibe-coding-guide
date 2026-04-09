# Write-Back Prompt

请基于当前切片的真实实现结果，完成 write-back。

至少同步：

- 当前 phase 或 planning doc 的完成情况
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md` 中与当前阶段有关的表述
- 若流程规则变化，更新 `design_docs/tooling/`
- 若到达安全停点，刷新 `.codex/handoffs/CURRENT.md`

请显式写明：

- 做了什么
- 验证了什么
- 哪些仍未验证
- 为什么现在可以停
- 下一条窄主线建议是什么
