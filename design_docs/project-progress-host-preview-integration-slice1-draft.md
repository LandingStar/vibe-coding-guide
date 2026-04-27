# Project Progress Host Preview Integration Slice 1 Draft

## 目标

让 VS Code extension 能直接打开当前 `.codex/progress-graph/latest.html`，把现有 progress graph preview 从 workspace artifact 提升为宿主内可见入口。

## 当前建议的 contract

1. 新增命令 `docBasedCoding.openProgressGraphPreview`
2. command 默认读取当前 workspace 的 `.codex/progress-graph/latest.html`
3. 若 artifact 缺失，panel 显示明确 fallback，而不是静默失败
4. 第一版直接复用现有 HTML preview，不新做第二套渲染层

## 当前建议的边界

1. 不做 preview 自动刷新
2. 不做 graph filtering / interaction controls
3. 不把 progress graph preview 做成新的 Activity Bar 常驻视图

## 当前判断

这条 slice 足够窄，因为它只验证宿主内消费是否成立，不会把范围扩到新的 renderer、状态同步或 richer host UX 设计。