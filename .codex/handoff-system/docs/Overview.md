# Project Handoff System Overview

## 1. 文档定位

本文件说明项目专用 handoff-system 的开发资产如何组织。

它服务于：

- 项目内 handoff skill 的后续实现
- handoff 模板、脚本与校验工具的放置边界
- 协议文档与项目内实现资产的主从关系

本文件不是 handoff 协议的 authoritative source。

handoff 协议本身应以：

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Session Handoff Conditional Blocks.md`

为准。

---

## 2. 当前目标

当前目标不是立刻实现完整 skill，而是先把以下基础固定下来：

- 协议文档落在 `design_docs/tooling/`
- handoff 实例产物落在 `.codex/handoffs/`
- 项目专用 skill 的开发资产落在 `.codex/handoff-system/`

这样后续继续做 skill、脚本或模板时，不会把：

- 协议定义
- 交接实例
- skill 实现细节

混在同一层。

当前已落地的第一份项目专用 proto-skill 为：

- `.codex/handoff-system/skill/project-handoff-generate/`
- `.codex/handoff-system/skill/project-handoff-accept/`
- `.codex/handoff-system/skill/project-handoff-refresh-current/`
- `.codex/handoff-system/skill/project-handoff-rebuild/`

其中生成端当前负责：

- 创建 canonical `draft` handoff
- 支持 `stage-close` / `phase-close`
- 校验生成结果的结构
- 在满足安全停点时允许由 model 主动进入 handoff 分支

其中接手端当前负责：

- 对 `CURRENT.md` 入口或指定 handoff 路径做只读 intake
- 输出 `ready / ready-with-warnings / blocked`
- 检查结构、authoritative refs 与最小 workspace warning

其中轮转端当前负责：

- 将 canonical `draft` 提升为 `active`
- 在存在旧 active handoff 时将其标记为 `superseded`
- 刷新 `.codex/handoffs/CURRENT.md` mirror
- 作为 handoff 分支中的连续下一步被 model 继续执行，只要上一步未返回 `blocked`

其中重建端当前负责：

- 在 `accept` 返回 `blocked` 后重跑 intake
- 写出 failure report
- 保留原失败 handoff
- 重建 replacement canonical `draft`

当前 handoff-system 的统一停止语义为：

- `blocked` 是 handoff 分支中的停止信号
- 若结果不是 `blocked`，model 可以继续执行下一条直接相关的 handoff 指令

它们当前仍不负责：

- 完全自动生成高质量 handoff 正文

---

## 3. 与协议文档的关系

本目录中的文档只负责解释：

- 项目内 handoff-system 怎样组织
- 项目内 skill 将来应如何实现 generate / accept / refresh current
- 后续脚本与测试应如何验证

它们不负责重新定义：

- handoff 类型
- core fields
- conditional blocks
- `Other` 规则

若本目录内容与 `design_docs/tooling/` 下的 handoff 协议文档冲突，应以前者中的协议文档为准。

---

## 4. 目录约定

当前目录约定如下：

- `docs/`
  - handoff-system 的项目内说明文档
- `templates/`
  - canonical handoff 模板
- `skill/`
  - 项目专用 skill 的实现位置
- `scripts/`
  - 结构校验、镜像刷新、辅助生成等脚本
- `tests/`
  - 针对脚本、模板与校验逻辑的本地测试
- `rehearsals/`
  - 官方受控演练样例与沙箱说明

其中跨项目安装入口为：

- `scripts/install_portable_handoff_kit.py`
- `docs/Portable Install.md`

handoff 实例本身不应放在本目录，而应继续放在：

- `.codex/handoffs/`

---

## 5. 推荐演进顺序

当前建议按以下顺序推进：

1. 协议文档与项目内说明文档
2. handoff 模板
3. 结构校验与草稿生成脚本
4. 项目专用生成端 skill
5. 项目专用接手端 skill
6. `CURRENT.md` 刷新脚本
7. fixtures 与自动化测试

不建议一开始就直接写完整 skill，而跳过协议、模板与校验。

---

## 6. 当前边界

本目录当前只应承载：

- 项目专用 handoff-system 的说明文档
- 预留模板
- 官方受控演练样例
- 未来 skill / script / test 的存放目录

本目录当前不应承载：

- 正式 handoff 协议定义
- 真实 handoff 历史产物
- 与 handoff 无关的其他 project automation

---

## 7. 相关文档

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Session Handoff Conditional Blocks.md`
- `.codex/handoffs/CURRENT.md`
