# Planning Gate: depends_on 依赖校验

- Status: COMPLETED
- Created: 2026-04-13
- Source: Checklist gap analysis #11
- Scope: pack manifest `depends_on` 字段的 runtime 消费

## 问题

当前 `depends_on` 字段：
- 已在所有 pack manifest 中声明（如 `project-local.pack.json` → `["doc-loop-vibe-coding"]`）
- 已由 `manifest_loader.py` 加载到 `PackManifest.depends_on: list[str]`
- 但 Pipeline / ContextBuilder 完全不消费它
- 如果依赖的 pack 未安装或未被发现，用户得到的是隐晦的导入/加载错误，而不是明确的"依赖 XYZ 未找到"

## 设计决策

### 校验策略

- **检查时机**：`Pipeline.from_project()` 中，在 `_discover_packs()` 收集所有 manifests 之后
- **检查方式**：每个 pack 的 `depends_on` 条目与已发现 pack name 集合做交集检查
- **失败策略**：未解析依赖 → **warning**（logging.warning + 结果记入 pack info），不阻塞加载
  - 理由：per `docs/pack-manifest.md`，"当前阶段只需表达依赖关系，不定义复杂解析算法"
  - pack 可能部分工作即使依赖缺失
- **不检查版本**：`depends_on` 解决"逻辑上依赖谁"，版本兼容由 `runtime_compatibility` 承担

### 结果暴露

- `Pipeline.info()` 中增加 `dependency_status` 字段（resolved / unresolved 列表）
- `check_constraints` 不增加新 ConstraintViolation（depends_on 不应阻塞治理链）
- 日志 warning 使 CLI 用户可见

### 特殊 pack 名称

- `"platform-core-defaults"` 是虚拟依赖（表示平台内建默认），不需要对应实际 manifest → 应被视为始终 resolved

## 切片

### Slice A: 核心校验

1. `src/pack/manifest_loader.py` 增加 `check_dependencies(manifests: list[PackManifest]) -> dict` 函数
   - 输入：已加载的所有 manifests
   - 输出：`{"resolved": [...], "unresolved": [{"pack": str, "missing_dep": str}, ...]}`
   - `"platform-core-defaults"` 视为始终 resolved
2. `Pipeline.from_project()` 或 `Pipeline.__init__()` 调用 `check_dependencies()`，logging.warning 未解析依赖
3. `Pipeline.info()` 返回中增加 `dependency_status` 字段
4. 测试：已解析依赖、未解析依赖、platform-core-defaults 特殊处理

### Slice B: 文档同步

1. `docs/pack-manifest.md` 更新 `depends_on` 节，注明 runtime 校验行为
2. `review/research-compass.md` 标记 gap #11 为已填充

## 验证门

- [ ] 正常项目（依赖已满足）：`info` 中 `dependency_status` 显示 all resolved
- [ ] 模拟缺失依赖：`info` 显示 unresolved + warning 日志
- [ ] `platform-core-defaults` 不被视为 unresolved
- [ ] 全套测试通过，zero regressions
