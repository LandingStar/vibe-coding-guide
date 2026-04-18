# Pack Internal Organization Standard

> 长期有效的 Pack 系统规范文档
> 来源：B-REF-3（Claude Skills best practices — progressive disclosure patterns）

## 原则

Pack 的引用文件是 agent 在运行时读取的上下文窗口内容。保持浅层、聚焦、可浏览的文件结构直接降低 token 消耗，提高 agent 理解效率。

## 引用深度规则

Pack manifest 中 `always_on` 和 `on_demand` 声明的文件称为"引用文件"。

- **深度 0**: manifest 本身
- **深度 1**: manifest 直接引用的文件（`always_on`/`on_demand` 中列出的路径）
- **深度 2+**: 引用文件内部再引用的其他文件

### 要求

- 引用深度 **不得超过 1**：引用文件不应包含运行时需要自动展开的嵌套引用
- 引用文件可以**提及**其他文件路径作为人类可读的指引，但 agent 不应需要递归读取才能理解引用文件的核心内容
- 如果某引用文件确实需要依赖另一文件的内容，应将两者合并为一个文件，或将被依赖内容提升为独立的 `always_on`/`on_demand` 条目

## 按域拆分规则

单个 always_on 文件不应承担多个不相关的职责。

### 要求

- 每个引用文件应聚焦于一个清晰的领域（workflow、delegation、conversation 等）
- 当一个文件开始覆盖两个以上独立主题时，应拆分为独立文件
- 推荐将相关引用文件放入 `references/` 子目录

### 推荐目录结构

```
my-pack/
  pack-manifest.json
  SKILL.md                  # 入口级 always_on（可选）
  references/
    workflow.md             # 核心工作流
    conversation.md         # 对话行为
    delegation.md           # 子 agent 委派
  scripts/                  # on_demand 脚本
  assets/                   # on_demand 资产（模板等）
  examples/                 # on_demand 示例
```

## 大文件 TOC 规则

### 要求

- 引用文件超过 **100 行**时，必须在文件顶部提供目录（Table of Contents）
- TOC 应列出所有二级标题（`##`），使 agent 能快速定位所需段落
- TOC 格式推荐使用 Markdown 链接列表

### 示例

```markdown
# Workflow Reference

## 目录

- [Core Loop](#core-loop)
- [Planning Rules](#planning-rules)
- [Execution Rules](#execution-rules)
- [Verification](#verification)

## Core Loop
...
```

## 验证检查项

以下检查项由 `validate_pack_organization()` 自动检测：

| 检查项 | 严重性 | 说明 |
|--------|--------|------|
| 引用文件不存在 | warning | always_on/on_demand 路径指向的文件不在 base_dir 中 |
| 引用文件超过 100 行无 TOC | warning | 缺少目录，agent 难以快速定位 |
| 嵌套引用模式 | warning | 引用文件中包含疑似自动展开引用的模式 |

## 与其他标准的关系

- **Pack Description Quality Standard**: 控制 manifest 的 `description` 字段质量
- **本标准**: 控制 pack 内部文件组织质量
- 两者共同确保 pack 在 METADATA → MANIFEST → FULL 各级别都提供高质量上下文
