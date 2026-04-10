# Planning Gate — Pack Runtime Loader

- Status: **CLOSED**
- Phase: 16
- Date: 2026-04-10

## 问题陈述

当前 PDP 5 个 resolver 的规则全部硬编码：
- `intent_classifier.py`：`_KEYWORD_MAP`（关键词→意图映射）、`IMPACT_TABLE`（意图→影响级别）
- `gate_resolver.py`：`_GATE_FOR_IMPACT`（影响→门）、`_ENTRY_FOR_GATE`（门→状态入口）
- `delegation_resolver.py`：`_DELEGATABLE_INTENTS`（可委托意图集合）
- `escalation_resolver.py`：`_LOW_CONFIDENCE`（低置信集合）+ 硬编码触发条件
- `precedence_resolver.py`：`_LAYER_PRIORITY`（层优先级）

`docs/pack-manifest.md` 和 `docs/plugin-model.md` 定义的 3 层配置覆盖机制（platform → instance → project-local）完全未实现。官方实例 `doc-loop-vibe-coding/pack-manifest.json` 已声明 intents、gates 等字段，但无 loader 消费。

## 设计策略

### 核心原则

1. **向后兼容**：无 pack 加载时，所有 resolver 使用当前硬编码默认值，行为不变
2. **规则可配置化**：每个 resolver 的硬编码规则提取为 `defaults`，可被 pack 上下文覆盖
3. **3 层叠加**：platform-default → official-instance → project-local，按 `_LAYER_PRIORITY` 排序
4. **Pack 只声明能力面**：manifest 是能力目录，规则正文独立存储

### 数据流

```
pack-manifest.json (platform)
  + pack-manifest.json (instance)  
    + pack-manifest.json (project-local)
      → ManifestLoader.load()
        → PackManifest dataclass
          → ContextBuilder.build()
            → PackContext dict
              → OverrideResolver.merge()
                → MergedRuleConfig
                  → PDP resolvers 消费
```

## 切片计划

### Slice A — ManifestLoader + PackManifest

**范围：**
- 创建 `src/pack/__init__.py`
- 创建 `src/pack/manifest_loader.py`：
  - `PackManifest` dataclass：name, version, kind, scope, provides, intents, gates, always_on, on_demand, depends_on, overrides, document_types, prompts, templates, validators, checks, scripts, triggers
  - `load(path: str | Path) -> PackManifest`：读取 JSON 文件 → 校验最小字段 → 返回 dataclass
  - `load_dict(data: dict) -> PackManifest`：从 dict 构建（测试友好）
  - 缺失可选字段用默认空值
- 测试：加载官方实例 manifest、最小 manifest、缺失字段、无效格式

### Slice B — ContextBuilder + PackContext

**范围：**
- 创建 `src/pack/context_builder.py`：
  - `PackContext` dataclass：manifests（按 kind 排序）、merged_intents、merged_gates、always_on_content（dict[filename, content]）
  - `ContextBuilder`：
    - `add_pack(manifest: PackManifest, base_dir: Path)`：注册一个 pack
    - `build() -> PackContext`：按层级排序 → 合并 intents/gates → 加载 always_on 文件内容
  - always_on 文件读取：相对于 pack base_dir 解析路径
- 测试：单 pack 构建、多层 pack 合并、always_on 文件加载、缺失文件处理

### Slice C — OverrideResolver + PDP 规则注入

**范围：**
- 创建 `src/pack/override_resolver.py`：
  - `RuleConfig` dataclass：
    - `keyword_map: dict[str, list[str]]`（intent classifier 用）
    - `impact_table: dict[str, str]`（intent classifier 用）
    - `gate_for_impact: dict[str, str]`（gate resolver 用）
    - `entry_for_gate: dict[str, str]`（gate resolver 用）
    - `delegatable_intents: set[str]`（delegation resolver 用）
    - `low_confidence_set: set[str]`（escalation resolver 用）
    - `layer_priority: dict[str, int]`（precedence resolver 用）
  - `resolve(context: PackContext) -> RuleConfig`：
    - 从 PackContext 中合并各层规则
    - 缺失项回退到硬编码默认值
  - `default_rule_config() -> RuleConfig`：返回当前硬编码默认值
- 重构 5 个 PDP resolver：
  - 每个 resolver 的 `resolve()` / `classify()` 新增可选 `rule_config: RuleConfig | None = None` 参数
  - `None` 时使用模块级默认值（向后兼容）
  - 非 `None` 时从 RuleConfig 读取规则
- 重构 `decision_envelope.build_envelope()`：新增可选 `rule_config` 参数，传递给各 resolver
- 测试：
  - 默认 RuleConfig 等价当前硬编码
  - 自定义 RuleConfig 改变分类/门/委派行为
  - 多层 override 场景
  - 全量回归确认向后兼容

**不做：**
- 不实现远端 pack 分发
- 不实现 pack 签名/校验
- 不实现 validators/checks/scripts/triggers 执行引擎（留给后续 Phase D）
- 不改变 PEP executor 接口（仅 PDP 侧消费 pack 规则）

## 验证门

1. `pytest tests/` 全部通过（无回归）——所有 253 项现有测试不受影响
2. ManifestLoader 可加载 `doc-loop-vibe-coding/pack-manifest.json`
3. ContextBuilder 可合并多层 pack 并加载 always_on 文件
4. OverrideResolver 可生成 RuleConfig 并被 PDP resolver 消费
5. 自定义 RuleConfig 可改变 intent classification / gate / delegation 行为
6. 无 pack 加载时行为与当前完全一致（向后兼容）
