# Phase 17 Authoring Documentation Standard Gate

## 1. 阶段定位

本阶段不新增新的 runtime 语义，也不扩张新的 effect authoring surface。

它的目标是把 `Phase 15-16` 已经落地的作者化入口，补上一套**长期、面向使用者**的文档标准。

---

## 2. 本阶段只回答的问题

在不继续扩 effect runtime 与 timeline 语义的前提下：

**作者化能力在本项目中，应以什么长期文档标准面向使用者。**

---

## 3. 实现边界

本阶段只做：

1. 固定作者化文档的长期放置位置
   - `design docs/stages/` 继续放阶段范围与验收
   - `design docs/tooling/` 继续放面向使用者的长期 usage guide
2. 固定作者化文档的最小章节模板
3. 固定“实现完成”与“使用文档完成”的联动规则
4. 固定 CLI / discovery surface 在作者化文档中的同步边界
5. 将当前 effect authoring 的两份 usage guide 整理成符合新标准的样例
6. 补一条最小自动检查，约束当前样例文档不偏离标准

本阶段明确不做：

1. 新的 timeline 调度语义
2. effect 脚本系统
3. 第二个 demo slice
4. 增量快照
5. rollback 改写
6. 大规模内容系统重构

---

## 4. 当前产物

当前阶段已落地：

- `design docs/tooling/Authoring Documentation Standard.md`
- 规范化后的：
  - `design docs/tooling/Effect Authoring Surface Usage Guide.md`
  - `design docs/tooling/Effect Runtime Hook Profile Usage Guide.md`
- `tests/support/authoring_docs.py`
- `tests/core/test_authoring_documentation_standard.py`
- `tests/acceptance/test_phase17_acceptance.py`

---

## 5. 当前验收标准

本阶段通过的标准是：

1. 作者化文档长期放置规则已经明确写入 tooling 文档
2. 当前作者化 usage guide 已统一采用同一套最小章节模板
3. “实现完成”与“使用文档完成”已被明确绑定
4. CLI / discovery surface 的同步边界已经写清
5. 当前样例文档已被自动检查约束

---

## 6. 为什么本阶段该停在这里

本阶段的重点是：

- 固定作者化文档标准
- 把现有样例整理成标准形式
- 为后续作者化工作建立长期、可复用的发现路径

如果继续往下做，就会进入另一类问题：

- 更外露的 metadata schema
- 更复杂的 runtime hook 组合
- 第二个内容切片
- 内容配置化 / 脚本化

这些都不再属于同一个“文档标准 gate”切片。

---

## 7. 对后续阶段的意义

若本阶段完成，则项目应具备：

- 一个长期稳定的作者化文档标准
- 一条“作者化代码 + 使用文档 + discovery surface”联动完成的规则
- 两份可作为后续文档模板直接复用的标准样例

这意味着后续作者化工作可以继续扩张，但不必再一边做功能一边重新发明文档形态。
