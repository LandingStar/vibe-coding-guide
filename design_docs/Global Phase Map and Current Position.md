# 全局阶段图与当前位置

## 文档定位

本文件用于解释 `doc-based-coding-platform` 当前处于哪个阶段，以及历史阶段文档应如何阅读。

## 推荐初始阶段划分

下面是当前仓库已经按现实收窄后的阶段划分：

- Phase 0：平台权威文档与官方实例定位定型
- Phase 1：当前仓库的 repo-local doc-loop adoption 对齐
- Phase 2：`doc-loop-vibe-coding/` 原型 authority rereview
- Phase 3：基于 rereview 结果推进 runtime/spec formalization 或 prototype cleanup

## 当前阶段判断

当前项目位置应表述为：

- Phase 0 已完成
- Phase 1 已在当前回合完成并收口
- Phase 2 的 prototype authority rereview 已完成首轮结论
- 当前停在重要设计节点的用户审核点
- 当前 active review doc 为 `design_docs/doc-loop-prototype-authority-rereview.md`

## 阅读顺序

1. 先读本文件。
2. 再读 `design_docs/Project Master Checklist.md`。
3. 再读当前 active planning 或 phase 文档。
4. 再读 `docs/README.md` 与相关权威文档。
5. 若需要当前仓库的切片与协议细节，再读 `design_docs/stages/README.md` 与 `design_docs/tooling/`。

## 当前结论

当前不应直接进入 prototype 深改或 runtime 扩写；应先等待用户审核 prototype authority rereview 结论，再决定下一条实现切片。
