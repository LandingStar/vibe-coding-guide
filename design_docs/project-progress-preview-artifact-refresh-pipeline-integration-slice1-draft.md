# Project Progress Preview Artifact Refresh Pipeline Integration Slice 1 Draft

## 目标

把 current standalone preview 的 refresh 从“读取旧 artifact”提升为“先调用现有 progress graph build/write helpers regenerate artifacts，再 reload panel”的最小宿主工作流。

## 当前建议的 contract

1. 复用 `tools.progress_graph` 现成的 `build_doc_progress_history` / `write_doc_progress_history` / `write_history_dot` / `write_history_html`
2. 由 extension 使用当前 workspace Python 执行 regenerate，不引入新后端
3. `Open Progress Graph Preview` 继续保持 reveal-or-create 行为
4. `Refresh Preview` 与 `refreshProgressGraphPreview` command 改为 regenerate + reload

## 当前建议的边界

1. 不新增 sidebar surface
2. 不新增 graph renderer
3. 不做 background file watcher
4. 不扩 projection source coverage

## 当前判断

这条 slice 足够窄，因为它只打通现有 preview artifact 的刷新链路，不改变 progress graph 的数据语义与展示架构。