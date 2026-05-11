# Commit Message（中文版）

```
release: 打包 v0.9.6 preview release，收口关系图谱工作

将当前关系图谱工作收口到新的 preview release 批次：runtime 与 official instance 同步到 0.9.6，VS Code extension 提升到 0.1.4，并把 G6 graph-view PoC、宿主并行预览和 Graph Config 交互一并纳入新的分发面。

## 变更

- 在 VS Code progress graph preview 中落地 G6 驱动的关系图谱 V2 预览，继续保留原始 baseline preview，并补齐 hover / click / 邻接高亮 / node detail / runtime binding 强调
- 补齐宿主交互：Reset Zoom/Pan、顶部 host chrome 折叠、Graph Config 收口为右上角浮条、metrics overlay 与左右分栏拖拽
- 修正 `Graph Config` 收起链路中的标题 jump / shrink / scrollbar 抖动，最终改为真实折叠按钮接管的淡入收口
- dual-package 与 release 文档同步推进到 `0.9.6`，extension 版本推进到 `0.1.4`
- 保持当前边界不变：`doc-based-coding-v0.9.6.zip` 继续只包含双 wheel 与 release 文档，VSIX 单独分发；control panel action semantics 仍留到下一条 planning line

## 验证

- `npm run build`：passed
- `release/verify_version_consistency.py`：All versions consistent
- `scripts/release.py --skip-tests --no-isolation`：生成 `release/doc-based-coding-v0.9.6.zip`，并同步新的 wheel / VSIX
```
