# Stage Docs Index

本目录按执行阶段与 planning gate 组织项目文档。

推荐子目录：

- `planning-gate/`
  - 下一条窄主线的候选文档
- `_templates/`
  - planning doc、phase doc 与手测指南模板

使用规则：

- 阶段范围、明确做什么/不做什么、验收与手测，统一放在 `design_docs/stages/`
- 长期协议与跨阶段规则，统一放在 `design_docs/tooling/`
- 当前项目位置先以 `../Global Phase Map and Current Position.md` 为准
- 若某个 planning-gate 候选被采纳，应复制或演化为正式 phase 文档，而不是只留在对话里
