# Planning Gate — Project Progress Preview Artifact Refresh Pipeline Integration

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-preview-workflow-integration-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-preview-workflow-integration.md` 已完成并关闭。

当前已经具备：

1. progress graph preview 已是 singleton 独立 WebView panel
2. panel 内已经有 `Refresh Preview` 与 `Reveal Artifact`
3. `.codex/progress-graph/latest.html` 可以被宿主直接消费

但当前 refresh 仍然只会重载现有 artifact，还不是 end-to-end refresh pipeline。

## 2. Scope

本 gate 只处理：

1. 从 VS Code extension 调用现有 progress graph artifact 生成链
2. 让 `Refresh Preview` 先 regenerate `.codex/progress-graph/latest.json` / `.dot` / `.html`，再 reload panel
3. 保持当前 standalone WebView panel，不新增 sidebar / renderer / graph semantics
4. `vscode-extension` build 与 artifact regenerate 验证

本 gate 不处理：

1. 新的 graph source projection
2. topic-aware linkage semantics
3. 更重的 preview interaction controls
4. 后台 watcher / auto-refresh daemon

## 3. Working hypothesis

当前最小可行路线应是：

1. 继续复用 `tools/progress_graph` 里现成的 `build/write` helpers
2. 从 extension 使用当前 workspace Python 直接调用这条生成链
3. 只把 `Refresh Preview` 提升为 regenerate + reload，不改变 `Open Preview` 的 reveal 行为
4. 先证明 end-to-end workflow 成立，再考虑更重的自动化刷新

## 4. Slices

### Slice 1 — Refresh pipeline contract

- 固定 regenerate target、Python 入口与 panel refresh boundary

当前状态：已完成；Slice 1 设计草案已创建为 `design_docs/project-progress-preview-artifact-refresh-pipeline-integration-slice1-draft.md`。

### Slice 2 — Extension integration

- 在 `vscode-extension` 中接入 artifact regenerate helper，并让 panel refresh 走 end-to-end workflow

当前状态：已完成。

### Slice 3 — Validation

- 运行 `npm run build`，并验证 progress graph artifacts 可 regenerate

当前状态：已完成。

## 5. Validation gate

- `Refresh Preview` 走 regenerate + reload
- `.codex/progress-graph/latest.json` / `.dot` / `.html` 可从 extension 使用的同一路径重建
- `vscode-extension` 的 `npm run build` 通过

## 6. Stop condition

- 当 standalone preview 的 refresh 成为 end-to-end workflow 且验证通过后停止
- 不在本 gate 内进入 watcher / daemon / sidebar 扩展

## 7. Completion note

- `vscode-extension/src/views/progressGraphArtifacts.ts` 已新增最小 artifact regenerate helper，复用 workspace Python 与 `tools.progress_graph` build/write 链
- `vscode-extension/src/views/progressGraphPreview.ts` 的 `Refresh Preview` 已升级为 regenerate + reload
- `vscode-extension` 的 `npm run build` 已通过
- 真实 workspace 已验证 `.codex/progress-graph/latest.json` / `.dot` / `.html` 可重新生成
- 后续方向分析已写为 `design_docs/project-progress-preview-artifact-refresh-pipeline-integration-followup-direction-analysis.md`