# Subagent Contract Prompt

你只负责以下窄切片，不负责扩 scope：

- 任务：`{{TASK}}`
- 可修改文件：`{{WRITE_SCOPE}}`
- 必须重读文档：`{{DOC_REFS}}`
- 验收标准：`{{ACCEPTANCE}}`
- 必跑验证：`{{VERIFICATION}}`
- 明确不做：`{{OUT_OF_SCOPE}}`

输出要求：

- 列出实际改动文件
- 列出运行过的验证与结果
- 列出未解决问题与假设
- 不要改写共享状态文档，除非合同显式授权
- 不要直接调用 `localTrajectory`，不要直接修改 Local Work Trajectory；如需汇报进度、阻塞、完成或建议推进动作，按 `docs/worker-trajectory-update-reporting.md` 写入 `Subagent Report.trajectory_update`
