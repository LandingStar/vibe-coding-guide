# Phase 17 Manual Authoring Documentation Standard Test Guide

## 1. 适用范围

本手测指南用于确认 `Phase 17` 的作者化文档标准已经真正落地。

由于本阶段不新增 runtime 语义，本手测重点是：

- 文档标准是否明确
- 当前样例是否已按标准整理
- 现有 discovery surface 是否仍然能把使用者引到正确入口

---

## 2. 文档检查

依次打开：

- `design docs/tooling/Authoring Documentation Standard.md`
- `design docs/tooling/Effect Authoring Surface Usage Guide.md`
- `design docs/tooling/Effect Runtime Hook Profile Usage Guide.md`

确认：

1. 标准文档已明确：
   - 长期放置位置
   - 最小章节模板
   - 实现完成与文档完成的联动规则
   - CLI / discovery surface 的同步边界
2. 两份 usage guide 都具有同一套 8 个章节
3. 两份 usage guide 的 `相关文档` 章节都能回到标准文档与对应阶段文档

---

## 3. 观察路径检查

在项目根目录运行：

```bash
python3.12 -m client.console_app
```

然后输入：

```text
effects
help effects
quit
```

预期：

- `effects` 仍能列出 effect definitions 与 runtime hook profiles
- `help effects` 仍可作为 discovery surface 的入口
- 当前作者化文档中的“发现与观察路径”说明与 CLI 表现一致

---

## 4. 自动化检查入口

建议至少运行：

```bash
python3.12 -m pytest -q \
  tests/core/test_authoring_documentation_standard.py \
  tests/acceptance/test_phase17_acceptance.py
```

这两组测试负责验证：

- 标准文档与 tooling 索引是否已登记
- 当前样例 usage guide 是否符合最小章节模板

---

## 5. 当前通过判定

满足以下条件即可判定 `Phase 17` 手测通过：

1. 标准文档内容完整
2. 两份样例 guide 已按统一模板整理
3. `effects / help effects` 的 discovery surface 仍然可用
4. 上述针对性测试通过
