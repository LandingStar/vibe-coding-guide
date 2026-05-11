# doc-based-coding v0.9.6 Preview Release (2026-05-10)

本次 `v0.9.6` preview release 以关系图谱工作为核心：把当前 G6 graph-view PoC、宿主并行预览、Graph Config 收起/展开交互和 metrics overlay 收口到同一批可分发产物里，同时把 runtime / official instance / extension 的 release 面统一推进到新的批次。

## 打包内容

| 产物 | 版本 | 说明 |
|------|------|------|
| `doc_based_coding_runtime-0.9.6-py3-none-any.whl` | 0.9.6 | 平台运行时，包含 CLI、MCP server、PDP/PEP、workflow、pack runtime |
| `doc_loop_vibe_coding-0.9.6-py3-none-any.whl` | 0.9.6 | 官方 doc-loop 实例 pack |
| `doc-based-coding-0.1.4.vsix` | 0.1.4 | VS Code 扩展，单独分发 |
| `doc-based-coding-v0.9.6.zip` | 0.9.6 批次 | 保持仅包含双 wheel 与 release 文档，不内嵌 VSIX |

## 本次版本重点

### 1. G6 关系图谱预览闭环

- 在 VS Code progress graph preview 中保留当前 baseline artifact 路线，同时并行挂载 G6 驱动的关系图谱 V2 预览面
- 当前关系图谱已稳定具备 hover / click / adjacency highlight / node detail / runtime binding 强调、zoom / pan、drag 和 Reset Zoom/Pan
- 图面浏览语言继续靠近 Obsidian graph-view，而不把当前切片直接扩成 control panel 动作面

### 2. 宿主交互与 Graph Config 收口

- 顶部 host chrome 当前可折叠收起，Graph Config 可从右侧卡片收口为右上角浮条
- metrics 已固定为图面顶部 overlay 摘要条，右侧分栏支持拖拽宽度调整
- `Graph Config` 标题交互已从跨容器移动方案回撤为更稳的本位 fade；收起侧最终改为真实折叠按钮接管，消除了 jump / shrink / scrollbar 抖动

### 3. 新 release 批次版本对齐

- runtime、instance、pack-manifest 与 release 文档统一同步到 `0.9.6`
- 官方实例 `__version__` 与 `runtime_compatibility` 约束同步到当前 release 批次
- VS Code extension 版本推进到 `0.1.4`，使当前图谱预览改动进入新的 VSIX 交付批次

### 4. 下一步方向保持清晰

- 本次 release 继续保持 read-only graph-view PoC 边界，不把 control panel action semantics 混入当前批次
- 当前批次打包完成后，下一条主线将以 control panel groundwork 为入口，而不是回头重开现有图谱预览闭环

## 验证结果

- `npm run build`：通过
- `release/verify_version_consistency.py`：All versions consistent
- `scripts/release.py --skip-tests --no-isolation`：生成新的双 wheel、`release/doc-based-coding-v0.9.6.zip` 与 `release/doc-based-coding-0.1.4.vsix`

## 安装顺序

```bash
pip install doc_based_coding_runtime-0.9.6-py3-none-any.whl
pip install doc_loop_vibe_coding-0.9.6-py3-none-any.whl
```

VS Code 扩展继续通过 "Install from VSIX" 安装 `doc-based-coding-0.1.4.vsix`。

完整变更历史见仓库根目录 `CHANGELOG.md`。
