# Project Handoff Validation

## 1. 文档定位

本文件定义项目专用 handoff-system 后续应具备的最小验证要求。

它关注的是：

- handoff 结构是否合格
- conditional blocks 是否触发正确
- `Other` 是否被误用
- `CURRENT.md` 是否保持与 canonical handoff 一致

本文件不替代正式协议文档，只负责定义项目内验证侧应检查什么。

---

## 2. 验证对象

项目专用 handoff-system 后续至少应验证以下对象：

- `.codex/handoffs/history/*.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/handoff-system/templates/*.md`
- `.codex/handoff-system/skill/*/scripts/*.py`
- 后续脚本与测试夹具

验证应覆盖：

- 文档结构
- block 命中
- 交接镜像一致性
- 异常样例

---

## 3. 结构校验

结构校验至少应检查：

- frontmatter 是否存在且字段齐全
- `kind` 是否只取允许值
- 正文章节是否完整且顺序正确
- `stage-close` / `phase-close` 的额外章节是否齐全
- `other_count` 是否与正文 `Other` 条目数一致

若 core fields 缺失，应直接视为失败，而不是仅给 warning。

---

## 4. Conditional Block 校验

conditional block 校验至少应检查：

- frontmatter 声明的 `conditional_blocks` 是否与正文一致
- 命中的 block 是否真的满足 trigger
- 已命中的 block 是否包含完整 required fields
- 明显命中的 block 是否被漏写

若 block 触发与正文内容冲突，应视为结构错误。

---

## 5. `Other` 误用校验

`Other` 是高风险区，应单独做严格校验。

至少应检查：

- 每条 `Other` 是否包含完整必填子字段
- 是否给出了有效的 `Why not fit existing fields`
- 其中内容是否其实属于 core fields
- 其中内容是否其实属于现有 conditional block

若 `Other` 只是把本应进入正式字段的内容“藏起来”，应判为失败。

---

## 6. `CURRENT.md` 镜像校验

`CURRENT.md` 应被视为 mirror，而不是独立事实源。

后续至少应检查：

- 当前是否存在唯一 active canonical handoff
- `CURRENT.md` 是否指向该 active canonical handoff
- `CURRENT.md` 与 source handoff 的关键字段是否一致
- 若 `CURRENT.md` 仍是 bootstrap placeholder，是否因此跳过正式镜像校验

一旦发现 `CURRENT.md` 与 active canonical handoff 不一致，应优先修复镜像，而不是修改协议文档解释差异。

---

## 7. Fixtures 与负例

项目专用 handoff-system 后续至少应保留两类夹具：

- 正例 fixtures
  - 合格的 `stage-close`
  - 合格的 `phase-close`
- 负例 fixtures
  - 缺失 core fields
  - 漏写 conditional block
  - `Other` 误用
  - `CURRENT.md` 指向错误 source

负例 fixtures 的目标不是“几乎合法”，而是稳定覆盖最常见的结构性错误。

当前最小自动化还应覆盖：

- `refresh current` 能把 `draft` 提升为 `active`
- `refresh current` 能把旧 `active` 标记为 `superseded`
- 轮转后 `accept --current` 可以读取新的 mirror
- `rebuild handoff` 能在 blocked intake 后写出 failure report
- `rebuild handoff` 能保留失败 source 并重建 replacement draft

若当前真实项目没有方便复现 blocked rebuild 的 live 场景，推荐优先使用：

- `.codex/handoff-system/rehearsals/rebuild-blocked-demo/`
- `.codex/handoff-system/scripts/create_rebuild_rehearsal_sandbox.py`

在独立 sandbox 中手动验证：

- `accept --current -> blocked`
- `rebuild --current -> ok`

---

## 8. 当前边界

本文件当前只定义：

- 项目专用 handoff-system 的最小验证面
- 将来脚本与测试应优先覆盖的问题类型

本文件当前不定义：

- 具体测试框架
- CLI runner
- 自动修复策略

这些内容应在后续脚本与测试真正落地时再补齐。
