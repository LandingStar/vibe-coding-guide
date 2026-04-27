# Project Progress Preview Workflow Integration Slice 1 Draft

## 目标

把 current progress graph preview 从“命令打开一个 HTML panel”提升为更像独立产品面的宿主 workflow：单例 WebView、可刷新、可定位 artifact，但仍保持在 editor area 单开，不挤进左侧窄侧栏。

## 当前建议的 contract

1. preview 保持 `WebviewPanel`，不转为 `WebviewView`
2. panel 采用 singleton/reveal 模式，重复打开时不创建新实例
3. panel 内提供 `Refresh Preview` 与 `Reveal Artifact` 两个最小动作
4. 继续复用 `.codex/progress-graph/latest.html`，不重写 graph renderer

## 当前建议的边界

1. 不做 Activity Bar 常驻 graph 面板
2. 不做 side bar 窄布局适配
3. 不做 graph filtering / zoom / interaction tools
4. 不把 preview 直接改造成 custom editor

## 当前判断

这条 slice 足够窄，因为它只提升宿主工作流层，不改变 progress graph 本身的生成链和 graph 语义层。