# Commit Message（中文）

```text
release: 发布 v0.9.9 安装态合同修复包

修复 consumeWorkerTrajectoryReport 在 wheel 安装态下错误地从
site-packages/docs 解析 Subagent Report schema 的问题，改为使用目标工作区
docs/specs/subagent-report.schema.json，并将 schema 与 worker 回写流程文档纳入
官方实例 bootstrap。

同时收口 Spirebound 全量测试暴露的协作证据语义：多 lane 只证明逻辑拆分，
不再被当作 scheduler/provider 并发证据。构建门新增隔离安装双 wheel、从安装
目录导入、bootstrap 临时工作区并通过 CLI 消费 worker report 的强制 smoke。
同时修复 pack hash 纳入根部 build/dist 生成物导致构建后 lock 漂移的问题。

本批次包含当前 readback/orchestration 基线，但不实现宿主反转；Direct/Managed
模式设施矩阵保留为后续待办。VSIX 无源码变更，保持独立版本 0.2.1。

验证：完整 release flow 通过，Python `2371 passed, 3 skipped`，隔离安装
smoke 与 Electron smoke 均通过，生成 `doc-based-coding-v0.9.9.zip`。
```
