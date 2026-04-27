# Planning Gate — Project Progress Host Preview Integration

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-external-reference-projection-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-external-reference-projection.md` 已完成并关闭。

当前已经有：

1. `.codex/progress-graph/latest.html`，可直接打开的自包含 preview artifact
2. internal factual layers、candidate layers 与 external-reference layer
3. `vscode-extension/`，现成的宿主 UX 薄层

但当前还有一个明显缺口：progress graph preview 仍然主要停留在 workspace artifact 层，没有进入宿主内直接可见的 UX surface。

## 2. Scope

本 gate 只处理：

1. VS Code extension 中的最小 progress graph preview 打开入口
2. 复用现有 `.codex/progress-graph/latest.html`，不新做第二套 renderer
3. command -> WebView panel 的最小集成
4. extension build 验证

本 gate 不处理：

1. 新的 graph renderer
2. richer interactive graph editing
3. preview 数据刷新自动化
4. 非 VS Code 宿主的第二实现

## 3. Working hypothesis

当前最小可行路线应是：

1. 在 `vscode-extension` 中新增一个 command
2. command 直接读取 `.codex/progress-graph/latest.html`
3. 用 WebView panel 承载现有 HTML artifact，而不是重写 preview UI
4. 第一刀先证明宿主内可见性成立，再决定是否继续做自动刷新或 richer integration

## 4. Slices

### Slice 1 — Panel contract

- 固定 command id、artifact path 与 missing-artifact fallback

当前状态：已完成；Slice 1 设计草案已创建为 `design_docs/project-progress-host-preview-integration-slice1-draft.md`。

### Slice 2 — Extension integration

- 在 `vscode-extension/src/views/` 中新增最小 preview panel helper
- 在 `extension.ts` / `package.json` 中注册命令

当前状态：已完成；已新增 `vscode-extension/src/views/progressGraphPreview.ts`，并在 `extension.ts` / `package.json` 中接入 `docBasedCoding.openProgressGraphPreview`。

### Slice 3 — Build validation

- 运行 `npm run build`

当前状态：已完成；`vscode-extension` 的 `npm run build` 已通过。

## 5. Validation gate

- `vscode-extension` 的 `npm run build` 通过
- command 能在宿主层提供 preview 打开入口

## 6. Stop condition

- 当宿主内 preview 打开入口成立且 extension 构建通过后停止
- 不在本 gate 内继续扩到自动刷新、interactive graph controls 或第二宿主