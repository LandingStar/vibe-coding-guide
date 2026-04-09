# Authoring Documentation Standard

## 1. 文档定位

本文件定义**作者化能力**面向使用者时的长期文档标准。

它解决的不是某个单独执行阶段的范围问题，而是：

- 作者化文档应长期放在哪里
- 最少应写哪些章节
- 什么情况下实现可被视为“真正完成”
- CLI / discovery surface 应如何与作者化文档联动

因此，本文件放在 `design docs/tooling/`，而不是 `design docs/stages/`。

---

## 2. 适用范围

本标准适用于所有后续会暴露给**引擎使用者**的作者化入口，包括但不限于：

- effect definition / registry / build
- runtime hook profile
- modifier / listener / scheduling 等后续作者化 surface
- 配套的 catalog / discovery / CLI 观察入口

本标准不直接定义：

- 阶段范围
- 运行时语义
- 程序模块边界

这些仍应分别放在对应的阶段文档、协议文档和代码结构中。

---

## 3. 长期放置规则

### 3.1 阶段文档

若本轮工作属于某个执行阶段，则以下内容放在：

- `design docs/stages/`

包括：

- 阶段范围
- 明确做什么 / 不做什么
- 手测指南
- 阶段验收标准

### 3.2 作者化使用文档

若文档的目标读者是**引擎使用者**，且重点是：

- 如何声明
- 如何注册
- 如何构建
- 如何发现 / 观察
- 当前支持边界是什么

则统一放在：

- `design docs/tooling/`

它们不应按阶段重新分目录，也不应被“大阶段”视角重新改写存储层级。

### 3.3 CLI / discovery surface

若作者化能力提供了：

- CLI 观察入口
- catalog 列表入口
- `help` 可发现入口

则它们仍属于运行时/CLI 资产，应继续维护在：

- `demo/command_reference.py`
- `design docs/CLI Command Reference.md`

而不是被重复抄写到作者化使用文档里当成第二套命令参考。

---

## 4. 最小章节模板

从本标准生效开始，面向使用者的作者化 usage guide 默认至少应包含下列章节：

1. `文档定位`
2. `适用范围与何时使用`
3. `入口位置`
4. `核心概念与声明结构`
5. `最小使用方式`
6. `发现与观察路径`
7. `当前边界`
8. `相关文档`

说明：

- 若某一项能力没有独立的 CLI / discovery surface，也应保留 `发现与观察路径` 章节，并明确说明当前的观察入口是什么，或说明“当前无独立入口”。
- 若某一项能力没有复杂结构，也不应删除 `核心概念与声明结构`，而应保持简短说明。
- 本模板追求的是长期可读、可比较、可维护，而不是把所有文档写成最大而全的手册。

---

## 5. 完成定义与联动规则

若某阶段新增或修改的是**作者化入口**，则实现完成不应只以代码合入为准。

默认还必须同步完成：

1. 至少一份符合本标准的 usage guide
2. `design docs/tooling/README.md` 中的入口登记
3. 对应阶段文档中的“如何使用 / 如何观察”说明
4. 若存在 CLI / discovery surface，则同步对应帮助、命令参考和回归

换句话说：

**作者化入口的“实现完成”与“使用文档完成”应被视为同一完成条件。**

---

## 6. 最小自动检查建议

本标准不要求一开始就建立复杂的文档工具链。

但至少应具备一条轻量自动检查，验证：

- 当前受本标准约束的 usage guide 是否存在
- 是否包含最小章节模板
- 是否已登记到 `design docs/tooling/README.md`

后续若作者化 surface 增长，再考虑把这部分提升成更完整的 tooling。

---

## 7. 当前标准样例

当前已按本标准整理的样例为：

- `Effect Authoring Surface Usage Guide.md`
- `Effect Runtime Hook Profile Usage Guide.md`

它们同时也是当前项目中 effect authoring 的标准发现入口。

---

## 8. 当前边界

本标准当前只解决：

- 存放位置
- 最小章节模板
- 作者化实现与文档的联动规则
- discovery surface 的同步边界

它当前**不**解决：

- 外部脚本格式标准
- 配置文件 schema 设计
- 内容包发布规范
- 第二个 demo slice 的作者化结构

这些都属于之后更深的 authoring / content surface 议题。
