# Planning Gate — Safe-Stop Writeback Bundle

- Status: `COMPLETED`
- Date: `2026-04-12`
- Owner: `GitHub Copilot`
- Scope: `safe-stop writeback bundle only`

## 1. Why This Slice Exists

当前仓库已经多次在真实 safe-stop 上执行 handoff generation、`CURRENT.md` refresh，以及 Checklist / Phase Map / direction / checkpoint 的多面同步。

这些动作目前已经有明确规则，但仍然是分步完成的：需要 main agent 手动判断哪些状态面要更新、何时算真正完成 safe-stop close、何时可以把 handoff 视为当前 canonical recovery 入口。

用户已明确把这件事标为 crucial，因此下一条最合理的窄切片，就是把 safe-stop close 收口成 first-class writeback bundle，而不是继续依赖逐项补写与人工串联。

## 2. Target Outcome

本切片完成后，应满足：

1. safe-stop close 有一份显式 bundle contract，最少覆盖 handoff generation、`CURRENT.md` refresh、Checklist、Phase Map、direction、checkpoint。
2. 该 bundle 明确哪些写回是必做项，哪些是条件项，避免把状态同步留给临场判断。
3. current safe-stop writeback 的标准流程有 targeted validation，避免再次出现“handoff 已生成但状态板仍显示待做”之类的不一致。

## 3. In Scope

- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/tooling/Session Handoff Standard.md`
- 需要时涉及的 handoff workflow 文档或 helper surfaces
- 与 safe-stop writeback bundle 直接相关的 runtime / tool / helper 改动
- 对应 targeted tests 与状态文档 write-back

## 4. Out of Scope

- 不扩展到通用外部 skill 接口能力。
- 不处理 `authority -> shipped copies` 单源编译 / 漂移检查子题。
- 不顺手重做 handoff branch invocation 语义；该部分已在前一切片收口。
- 不进入 driver / adapter / 转接层 backlog。

## 5. Validation

至少完成以下验证：

1. targeted tests 覆盖 safe-stop bundle 的必做写回面。
2. 相关协议文档、状态文档与 handoff surface 不出现互相矛盾的口径。
3. 相关改动文件无错误。

## 6. Risks

- 若 bundle 边界定义过宽，容易把本应条件执行的写回也硬绑定进去。
- 若只定义协议、不补验证，仍可能再次退回到人工逐项补写。

## 7. Exit Condition

当 safe-stop close 已具备可复用的 bundle contract，且至少一次通过 targeted validation 证明 handoff 与状态文档可以一致收口时，本切片即可停止。

## 8. Execution Results

- 已新增 `src/workflow/safe_stop_writeback.py`，把 safe-stop close 收口为结构化 bundle contract：显式区分 required steps、conditional steps、当前方向文档路径与 `files_to_update`。
- `src/mcp/tools.py` 的 `writeback_notify()` 现已直接返回 `safe_stop_writeback_bundle`，并把 `auto_next.files_to_update` 改为从 bundle contract 派生，不再只靠固定三项文件列表。
- bundle 的默认必做面已覆盖：canonical handoff generation、`CURRENT.md` refresh、Checklist、Phase Map、当前方向候选文档、checkpoint。
- bundle 的默认条件项已覆盖：清除 active planning-gate 标记、supersede 旧 active canonical handoff、以及当语义变化时同步 workflow / handoff 协议文档。
- 权威协议与 shipped 副本已同步：当前仓库、bootstrap 与 example 的 workflow / handoff 标准现在都明确把 safe-stop writeback 视为 bundle，而不只是零散状态补写。

## 9. Validation Results

- `get_errors`：helper、MCP 工具、测试文件以及相关协议文档均无错误。
- `pytest tests/test_safe_stop_writeback.py tests/test_mcp_tools.py -q`：`27 passed`。
- 已新增 targeted tests：
	- `tests/test_safe_stop_writeback.py` 覆盖 direction doc 发现、required/conditional bundle items。
	- `tests/test_mcp_tools.py` 覆盖 `writeback_notify()` 返回的 safe-stop bundle contract 与 `files_to_update`。