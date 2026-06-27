# 2026-04-19 测试规则与文档库结构建议说明

## 目标

- 在不进入实际优化的前提下，补一套当前专用于 `DOC-BASED CODING` 插件测试的规则和文档库结构建议。

## 本轮新增内容

- `testing/README.md`
- `testing/rules/Suggested Testing Rules.md`
- `testing/plans/README.md`
- `testing/reports/README.md`
- `testing/issues/README.md`
- `testing/scenarios/README.md`
- `testing/archive/README.md`
- `testing/_templates/` 下六份模板

## 设计取向

- 整体语气偏“建议”，尽量避免写成硬性规范。
- 结构设计偏轻量，适合先沉淀插件测试事实和反馈。
- `testing/` 当前优先服务于这个插件本身，后续成熟后也许再抽象成通用组件。
- `testing/` 可以独立使用，也可以先当作对现有 `review/` / `feedback/` 的补充模板库。

## 结论

- 当前已经具备一套最小可用的插件测试文档库结构。
- 如果后续仍以插件测试为主，也许可以继续沿这套结构整理新的计划、报告和问题反馈。