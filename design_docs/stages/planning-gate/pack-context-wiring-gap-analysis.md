# Planning Gate: Pack Context 下游接线

> 状态: **pending** — 间隙分析完成，待排期实施  
> 来源: 2026-04-10 pack manifest 字段间隙分析  
> 前置: checkpoint-persistence 完成后可启动

## 背景

对 `docs/pack-manifest.md` 规范定义的全部字段进行了端到端追踪，发现绝大多数字段在 ManifestLoader 加载后即成为死数据——ContextBuilder 合并了部分字段但无下游消费者，扩展件字段完全不连接 ValidatorRegistry 等已有基础设施。

## 字段间隙全表

| # | 字段 | Loader | ContextBuilder | OverrideResolver | PEP/PDP | 官方实例值 | 间隙 |
|---|------|:------:|:--------------:|:----------------:|:-------:|-----------|------|
| 1 | `name` | ✅ | 存于 manifests | ❌ | ❌ | `doc-loop-vibe-coding` | 仅存储 |
| 2 | `version` | ✅ | 存于 manifests | ❌ | ❌ | `0.1.0-prototype` | 仅存储 |
| 3 | `kind` | ✅ | ✅ 排序用 | ❌ | ❌ | `official-instance` | 间接消费（排序） |
| 4 | `scope` | ✅ | ❌ | ❌ | ❌ | 描述字符串 | 完全未消费 |
| 5 | `provides` | ✅ | → merged_provides | ❌ | ❌ | 7 种能力 | 合并但死数据 |
| 6 | `document_types` | ✅ | → merged_document_types | ❌ | ❌ | 7 种文档类型 | 合并但死数据 |
| 7 | `intents` | ✅ | → merged_intents | ❌ | ❌ | 10 种 intent | 合并但死数据 |
| 8 | `gates` | ✅ | → merged_gates | ❌ | ❌ | 3 种 gate | 合并但死数据 |
| 9 | `always_on` | ✅ | → always_on_content | ❌ | ❌ | 3 个文件 | 内容已读取但无注入 |
| 10 | `on_demand` | ✅ | ❌ 不处理 | ❌ | ❌ | 14 个条目 | 最大间隙 |
| 11 | `depends_on` | ✅ | ❌ | ❌ | ❌ | `["platform-core-defaults"]` | 完全未校验 |
| 12 | `overrides` | ✅ | ❌ | ❌ | ❌ | `[]` | 未消费 |
| 13 | `prompts` | ✅ | ❌ | ❌ | ❌ | 4 个路径 | 无注册桥接 |
| 14 | `templates` | ✅ | ❌ | ❌ | ❌ | 3 个目录 | 无注册桥接 |
| 15 | `validators` | ✅ | ❌ | ❌ | ❌ | 2 个脚本 | Registry 存在但无自动填充 |
| 16 | `checks` | ✅ | ❌ | ❌ | ❌ | `[]` | 类似 validators |
| 17 | `scripts` | ✅ | ❌ | ❌ | ❌ | 3 个脚本 | 无执行入口 |
| 18 | `triggers` | ✅ | ❌ | ❌ | ❌ | `["chat"]` | Registry 存在但无自动填充 |
| 19 | `rules` | ✅ | → merged_rules | ✅ → RuleConfig | ✅ PDP | 未设置 | **唯一贯通路径**，但官方实例空转 |

## 发现

1. **唯一贯通路径**: `rules` → merged_rules → RuleConfig → PDP resolvers
2. **"写入未读取"**: ContextBuilder 产出 `merged_intents/gates/document_types/provides`，但无消费者
3. **扩展件桥接缺失**: ValidatorRegistry/TriggerRegistry 已就绪，manifest 无自动注册
4. **on_demand 完全断裂**: Loader 存了路径列表，ContextBuilder 不读取也不提供懒加载 API
5. **官方实例 rules 为空**: 唯一贯通路径在实际使用中也是空转

## 建议实施切片

### 切片 A: PackContext → PDP 接线（高价值）
- `merged_intents` 注入 intent_classifier 的 `platform_intents`
- `merged_gates` 注入 gate_resolver 合法值集合
- `merged_provides` 用于 delegation 能力检查

### 切片 B: always_on 内容注入
- 定义 prompt context 组装接口
- PackContext.always_on_content → system prompt 上下文

### 切片 C: on_demand 懒加载 API
- ContextBuilder 增加 `load_on_demand(key)` 方法
- 按需读取文件内容并缓存

### 切片 D: 扩展件 → Registry 桥接
- PackRegistrar: 读 manifest.validators/checks/triggers，自动注册到 ValidatorRegistry
- prompts/templates/scripts 的加载与索引

### 切片 E: 依赖校验
- pack 注册时验证 depends_on 列表中的 pack 已加载

## 涉及文件

- `src/pack/context_builder.py`
- `src/pack/override_resolver.py`
- `src/pdp/intent_classifier.py`
- `src/pdp/gate_resolver.py`
- `src/pep/executor.py`
- `src/validators/registry.py`
- `doc-loop-vibe-coding/pack-manifest.json`
