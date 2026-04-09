# Tooling Docs Index

本目录收纳**跨阶段长期存在**的开发工具与工具链文档。

这里的文档不属于某一个执行阶段，因此：

- 不应归档到 `design docs/stages/`
- 不应按阶段命名驱动目录层级
- 可以被多个阶段反复引用

当前文件：

- `Authoring Documentation Standard.md`
- `Session Handoff Standard.md`
- `Session Handoff Conditional Blocks.md`
- `Verification Platform Seed and Tooling Standards.md`
- `Effect Authoring Surface Usage Guide.md`
- `Effect Runtime Hook Profile Usage Guide.md`

说明：

- 若某项能力同时具有“阶段性建设切片”和“长期工具链”双重身份：
  - 阶段范围、边界、验收放在 `design docs/stages/`
  - 长期定义、分层标准、晋升规则放在 `design docs/tooling/`
- 若某项能力属于**作者化入口**，则面向使用者的 usage guide 也应统一落在本目录，并遵循：
  - `Authoring Documentation Standard.md`
- 若某项能力属于**多会话协作协议**，则长期协议文档也应统一落在本目录；
  - 对应的项目专用实现资产、模板、脚本与 skill 开发文档，应放在 `.codex/handoff-system/`
  - `design docs/tooling/` 只负责协议定义与长期规则，不承载项目内 skill 实现细节
