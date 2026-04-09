# 全局阶段图与当前位置

## 文档定位

本文件用于解释 `{{PROJECT_NAME}}` 当前处于哪个阶段，以及历史阶段文档应如何阅读。

## 推荐初始阶段划分

下面是一套可直接起步的默认划分，后续应按项目现实更新：

- Phase 0：文档闭环与协作协议 bootstrap
- Phase 1：第一条可执行窄主线
- Phase 2：验证、写回与协作加固

## 当前阶段判断

当前项目位置应表述为：

- Phase 0 已完成 bootstrap
- 当前重新回到下一执行阶段启动前的 planning gate

若已经开始具体功能实现，应把本节改成项目自己的真实阶段口径，而不是继续沿用模板文字。

## 阅读顺序

1. 先读本文件。
2. 再读 `design_docs/Project Master Checklist.md`。
3. 再读 `design_docs/stages/README.md`。
4. 再进入 active planning 或 phase 文档。
5. 若需要协议细节，再读 `design_docs/tooling/`。

## 当前结论

当前不应直接开始无边界编码；应先定义下一条窄切片，并把阶段目标、边界、验证与 write-back 方式写入 planning-gate 文档。
