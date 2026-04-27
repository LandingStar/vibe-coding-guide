# Planning Gate — Project Progress Preview Workflow Integration

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-research-compass-topic-projection-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-research-compass-topic-projection.md` 已完成并关闭。

当前已经具备：

1. `vscode-extension` 里的 `docBasedCoding.openProgressGraphPreview` 命令
2. `.codex/progress-graph/latest.html` 的宿主内独立 WebView 打开入口
3. richer `research-compass-current` graph，包括 entry layer 与 topic layer

但当前 preview workflow 仍然偏弱：

1. 每次都是一次性新开 panel
2. 没有 refresh / reveal artifact 这种工作流动作
3. panel 还不像独立产品面，更像“临时打开一个 HTML 文件”

## 2. Scope

本 gate 只处理：

1. 将 progress graph preview 升级为 singleton 独立 WebView panel
2. 在 panel 内提供 refresh / reveal artifact 工作流
3. 保持 preview 在 editor area 单开，而不是落到左侧窄侧栏
4. `vscode-extension` build 验证

本 gate 不处理：

1. Activity Bar 常驻 graph view
2. 第二套 graph renderer
3. topic-aware cross-graph semantics
4. richer graph interaction controls

## 3. Working hypothesis

当前最小可行路线应是：

1. 把 `progressGraphPreview.ts` 从一次性 helper 提升为 singleton panel controller
2. 复用现有 `.codex/progress-graph/latest.html`，但加一层宿主工作流 shell
3. 用 `refresh` / `reveal artifact` 提供最小的产品级 workflow，而不是再增加左侧侧栏承载
4. 第一刀只证明独立 WebView workflow 成立，不扩到更重的 sidebar surface

## 4. Slices

### Slice 1 — Panel workflow contract

- 固定 singleton panel、refresh、reveal artifact 的最小边界

当前状态：已完成；Slice 1 设计草案已创建为 `design_docs/project-progress-preview-workflow-integration-slice1-draft.md`。

### Slice 2 — Extension implementation

- 在 `vscode-extension` 中实现 panel controller 与相关 commands

当前状态：已完成。

### Slice 3 — Build validation

- 运行 `npm run build`

当前状态：已完成。

## 5. Validation gate

- progress graph preview 变成可复用的独立 WebView panel
- panel 内具备 refresh / reveal artifact workflow
- `vscode-extension` 的 `npm run build` 通过

## 6. Stop condition

- 当独立 WebView workflow 成立且 build 通过后停止
- 不在本 gate 内扩展到 Activity Bar 常驻图视图

## 7. Completion note

- `vscode-extension/src/views/progressGraphPreview.ts` 已升级为 singleton panel controller，并在 panel 内提供 `Refresh Preview` / `Reveal Artifact`
- `vscode-extension/src/extension.ts` 与 `vscode-extension/package.json` 已补齐 workflow commands
- `npm run build` 已通过
- 后续方向分析已写为 `design_docs/project-progress-preview-workflow-integration-followup-direction-analysis.md`