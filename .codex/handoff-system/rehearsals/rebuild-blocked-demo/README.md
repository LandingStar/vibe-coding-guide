# Rebuild Blocked Demo

本目录提供一套官方演练样例，用于手动验证 handoff rebuild 的成功路径，而不污染当前项目的真实 handoff 流。

## 目的

这套样例用于覆盖这样一条真实操作链：

1. `CURRENT.md` 指向一个 canonical handoff
2. 该 canonical handoff 因 authoritative ref 缺失而在 `accept` 中返回 `blocked`
3. handoff rebuild skill 基于该 blocked source 写出 failure report
4. handoff rebuild skill 重建出新的 canonical `draft`

## 内容

- `source/blocked-phase-close.md`
  - 一个结构合法但故意引用缺失 ref 的 canonical handoff 样例
- `../../scripts/create_rebuild_rehearsal_sandbox.py`
  - 将本样例展开为临时 git 仓库的辅助脚本

## 推荐用法

先创建演练 sandbox：

```bash
python .codex/handoff-system/scripts/create_rebuild_rehearsal_sandbox.py
```

脚本会输出一个新的 sandbox 路径与 `suggested_commands`。优先直接复制脚本输出的命令；它会自动指向当前仓库里的 accept / rebuild 脚本。

若需要手动拼命令，请将 `<repo-root>` 替换为当前 handoff-system 所在项目根目录：

```bash
python <repo-root>/.codex/handoff-system/skill/<...-handoff-accept>/scripts/intake_handoff.py --current --json
python <repo-root>/.codex/handoff-system/skill/<...-handoff-rebuild>/scripts/rebuild_handoff.py --current --json
```

预期结果：

- 第一步 `accept --current` 返回 `blocked`
- 第二步 `rebuild --current` 返回 `ok`
- sandbox 内会新增：
  - `.codex/handoffs/reports/*.json`
  - `.codex/handoffs/history/*_rebuild.md`

## 边界

本目录只服务于手动演练与受控验证。

不要：

- 将其中样例直接当作真实项目 handoff 使用
- 在真实项目根目录里直接拿它覆盖现有 `CURRENT.md`
