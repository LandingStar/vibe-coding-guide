# Portable Install

## 1. 文档定位

本文件说明如何把当前项目里的 handoff system 安装到其他仓库中。

这一安装流程的目标是：

- 复制 handoff 协议文档
- 复制 `.codex/handoff-system/` 实现资产
- 初始化 `.codex/handoffs/`
- 为目标仓库生成不冲突的 slash skill 名

它不负责：

- 自动改写目标项目的 `AGENTS.md`
- 自动生成目标项目自己的阶段文档
- 自动产出第一份真实 handoff

---

## 2. 推荐命令

从当前仓库根目录运行：

```bash
python .codex/handoff-system/scripts/install_portable_handoff_kit.py --target-repo <target-repo> --register
```

可选参数：

- `--skill-prefix <prefix>`
  - 指定目标仓库的 skill 前缀；默认取目标仓库目录名并做 slug 化
- `--force`
  - 在安全前提下覆盖已存在的 protocol docs 或 `.codex/handoff-system/`

---

## 3. 安装结果

安装后，目标仓库至少会得到：

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Session Handoff Conditional Blocks.md`
- `.codex/handoff-system/`
- `.codex/handoffs/history/`
- `.codex/handoffs/reports/`
- `.codex/handoffs/CURRENT.md`
- `.github/skills/`

其中：

- `CURRENT.md` 初始为 bootstrap placeholder
- `Project Master Checklist.md`
- `Global Phase Map and Current Position.md`

若目标仓库原先不存在，也会生成最小占位文档，供后续补齐。

---

## 4. Skill 命名

为避免多个项目同时暴露多个 handoff workflows，installer 会把项目级 skill 名命名为：

- `<prefix>-handoff-generate`
- `<prefix>-handoff-accept`
- `<prefix>-handoff-refresh-current`
- `<prefix>-handoff-rebuild`

例如目标仓库名是 `sample-game`，则 slash skill 会变为：

- `/sample-game-handoff-generate`
- `/sample-game-handoff-accept`
- `/sample-game-handoff-refresh-current`
- `/sample-game-handoff-rebuild`

---

## 5. 安装后建议

安装完成后，建议立即做三件事：

1. 补齐 `design_docs/Project Master Checklist.md`
2. 补齐 `design_docs/Global Phase Map and Current Position.md`
3. 在新的 Copilot chat 会话里确认新的 slash skill 已经出现

然后再开始第一份真实 handoff 的生成与轮转。
