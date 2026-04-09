# Stage Docs Index

本目录用于按**全局阶段**重新组织项目文档。

当前阶段树如下：

- `mvp/`
  - Phase 1：MVP 基线阶段
- `host-separation-and-diagnostics/`
  - Phase 2：宿主分离与诊断阶段
- `multi-scheduler-expansion/`
  - Phase 3：多调度扩展阶段
- `runtime-hardening/`
  - Phase 5、Phase 8：运行时恢复与加固阶段
- `scheduling-deepening/`
  - 旧入口跳转页，timeline 调度深化执行文档已并入 `timeline_T1/`
- `timeline_T1/`
  - post-MVP 至 Phase 12 的 timeline 主线文档包
  - 其中 `timeline_T1/scheduling-deepening/` 收纳原 `Phase 6-7、9-12` 执行文档
- `verification-and-determinism/`
  - Phase 14：验证平台雏形与 cross-driver determinism matrix
- `authoring-surface/`
  - Phase 15-16：effect authoring surface 与 runtime hook profile
- `planning-gate/`
  - 规划门与候选 backlog

说明：

- 设计闭合阶段的主题文档仍保留在 `design docs/` 根层，因为它们按主题组织更自然，不适合强行拆进阶段目录。
- 跨阶段长期工具链文档应放在 `design docs/tooling/`，而不是并入 `stages/`。
- 已执行阶段文档保留原文件名与原正文，仅通过目录与索引重新归类。
- 当前项目位置请先阅读：
  - `../Global Phase Map and Current Position.md`
