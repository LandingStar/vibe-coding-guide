# Progress Graph 局部工作轨迹图 UI 需求

## 文档定位

本文记录当前关于 progress graph 展示方式重设的 UI 需求结论。

它只固定展示语义与交互目标，不定义后端 schema、调度 runtime、真实 agent 并行模型，也不把讨论扩展为 agent 集群方案。

相关入口：

- `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`
- `design_docs/project-progress-multi-graph-direction-analysis.md`
- `design_docs/project-progress-multi-graph-slice1-draft.md`

## 背景

当前 progress graph preview 中，`checkpoint-current` 与 `project-checklist-current` 不是数据重复，但用户观感上容易混淆。

进一步讨论后，当前判断是：问题不在于两份数据是否重复，而在于它们不应继续使用同一种图形语法平铺展示。

展示层应区分：

1. 全局项目结构图
2. 某个顶层局部工作的推进状态图

## 展示分工

### 全局项目结构图

全局图更适合使用关系图谱形式。

原因：

1. 全局工作单元、planning gate、文档、发布物、证据、依赖与后续方向之间天然形成网状关系。
2. 全局图中的独立节点或节点团更可能具有较强并行性。
3. 关系图谱适合回答“项目结构是什么、哪些工作之间有关联、哪些方向可以并行推进”。

当前倾向：

- 全局图应成为默认主入口。
- 当前 `project-checklist-current` 更接近全局图的数据来源语义。
- 全局图可继续使用 `knowledge-graph-engine` 的关系图谱渲染方式。

### 局部工作轨迹图

局部图不应默认继续使用自由力导向关系图谱。

局部工作通常具有明显的推进轨迹：开始、拆分、等待、验收、验证、写回、交接、合流。它可能不是单线，但也不是全局图那样的任意网络，更像若干条相互依赖的工作线。

当前倾向：

- 局部图应使用“工作轨迹图”形式。
- 它表达一个顶层工作内部的推进状态。
- 它不是普通并行泳道图；多线不自动表示真实并行。
- 它不是纯 agent 图；线的边界由相对独立的上下文和工作分割共同决定。

## 局部工作轨迹图语义

### 工作线

一条工作线代表一个相对独立的上下文工作线。

工作线的成立条件：

1. 该线承载一套相对连续、可独立追踪的上下文。
2. 该线对应顶层局部工作内部的一段可分割工作。
3. 该线可以被单独推进、等待、验收、交接或合流。
4. 该线不要求一一对应某个 subagent。

工作线与 agent 的关系：

1. subagent 可以承接某条工作线，但不是工作线的定义依据。
2. 一条线可以先后由不同执行上下文或 subagent 承接。
3. 一个执行上下文或 subagent 也可能处理多条线。
4. UI 不应把“多条线”默认解释为“多个真实 agent 正在并行执行”。

### 线头标签

每条工作线头部显示一个短标签。

短标签用于快速扫视，不承载完整任务描述。

示例：

- `接口适配`
- `验证`
- `文档回写`
- `发布`
- `状态同步`
- `组件需求`

详细信息应放入 hover、侧栏或节点详情中，例如：

1. scope
2. 关联文档
3. 当前状态
4. 等待对象
5. 最近事件
6. 承接执行上下文或 subagent

### 事件节点

工作线由事件节点串联。

首批建议节点类型：

1. `start`：工作线起点
2. `task`：普通工作推进节点
3. `decision`：方向或边界决策
4. `review`：验收或审查点
5. `wait`：等待其他线、外部输入或验证结果
6. `validation`：测试、构建、人工 spot check 等验证点
7. `writeback`：文档、状态板、handoff 或 artifact 写回
8. `handoff`：上下文交接
9. `merge`：合流或吸收另一条线结论
10. `close`：该线完成或停止

### 跨线关系

跨线关系用于表达局部工作内部的耦合。

建议边类型：

1. `depends_on`：依赖另一条线的结果
2. `waits_for`：显式等待
3. `unblocks`：解除另一条线阻塞
4. `hands_off`：交接上下文或产物
5. `syncs_from`：吸收另一条线的信息或结论
6. `merges_into`：合流到另一条线
7. `proposes_new_line`：某条线提出新增工作线
8. `approves_new_line`：指导上下文批准新增工作线

这些关系应优先帮助用户理解“为什么某条线在等待、为什么新线出现、为什么两条线合流”，而不是制造全局图式的复杂网状视觉。

## 指导上下文与线管理

一个局部工作应存在一个指导上下文，用于管理该局部图的结构演化。

指导上下文职责：

1. 在工作开始时开设一条或多条初始工作线。
2. 为初始工作线放置初始节点。
3. 审查每个关键节点是否满足验收条件。
4. 审查后续节点是否应开设。
5. 在需要时开设新工作线。
6. 接收工作线提出的新线需求，并决定批准、修改或拒绝。
7. 在必要时指导合流、交接或停止。

UI 可选表现：

1. 显示为顶部轻量指导线，用于呈现开线、验收、批准、拒绝、合流决策。
2. 或作为节点上的审查/批准标记与详情层信息呈现。

当前未固定指导上下文必须以独立可见线展示；只固定其语义必须存在，否则中途开线、节点验收与合流缺少可解释来源。

## 动态开线

局部工作轨迹图必须支持运行中新增工作线。

UI 需求：

1. 新线可以在工作中途出现，而不是必须从图最左侧开始。
2. 新线出生点应能追溯到触发它的事件节点。
3. 如果新线由某条工作线提出，应表达 proposal -> review -> approved/rejected 的关系。
4. 被批准的新线应从批准点或触发点附近开始，避免画成一条从起点空置至中途的长线。
5. 新线头部同样只显示短标签，详细 scope 与原因进入详情层。

## 视觉原则

1. 局部图应以线性推进为主，允许少量跨线耦合。
2. 多线不等于真实并行，应通过状态和线段样式区分 active、waiting、blocked、done。
3. 等待态应可见，但不应喧宾夺主。
4. 跨线边应尽量少而语义明确。
5. 工作线标签保持短，细节下沉到交互层。
6. 全局关系图与局部工作轨迹图应使用不同视觉语法，避免用户误以为两类图只是数据重复。

## 非目标

1. 不在本文定义后端存储模型。
2. 不在本文定义调度器、agent runtime 或真实并行执行模型。
3. 不要求每条工作线对应一个 subagent。
4. 不要求把当前 `checkpoint-current` 立即迁移为该 UI。
5. 不要求修改外部 `knowledge-graph-engine` 关系图谱组件。
6. 不记录或扩展 agent 集群设想；本文只讨论图形展示语义。

## 后续待讨论

后端实现讨论应从以下问题切入：

1. 局部工作轨迹图的数据结构是否应独立于当前 progress graph 多图模型。
2. 工作线、事件节点、跨线关系和指导上下文应如何持久化。
3. 当前 checkpoint、handoff、planning gate、work log 中哪些信息可以投影为事件节点。
4. 动态开线与节点验收应由事件日志推导，还是由显式状态模型记录。
5. 全局图节点如何绑定到一个或多个局部工作轨迹图。

## 2026-06-04 后端最小单线切片

用户进一步修正推进顺序：应先完成后端实现，再做 UI 绑定；第一步只需要相对简易的功能，支持单线并先跑起来。

本轮已落地最小 backend-first 能力：

1. 新增 `tools/progress_graph/trajectory.py`。
2. 新增 `LocalWorkTrajectory`、`TrajectoryLane`、`TrajectoryEvent`、`TrajectoryRelation`。
3. 新增 `build_checkpoint_work_trajectory(project_root)`：把当前 `.codex/checkpoints/latest.md` 的 `Current Todo` 投影为单条 `lane:main` 上的顺序事件。
4. 新增 `write_checkpoint_work_trajectory(project_root)`：写出 `.codex/progress-graph/local-work-trajectory.json`。
5. 新增 `load_local_work_trajectory(project_root)` 与 `trajectory_json_path(project_root)`。
6. 当前只支持单线、顺序事件和 `sequence` 关系；不支持多线、动态开线、指导线可视化、UI 绑定或真实调度接入。
7. 新增 `tests/test_progress_graph_trajectory.py` 覆盖单线投影、JSON round-trip 与引用校验。

当前 focused validation：

1. `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过，`3 passed`。
2. `python -m pytest tests/test_progress_graph.py tests/test_progress_graph_doc_projection.py -q` 通过，`10 passed`。

## 2026-06-04 UI 技术路线修正

用户要求先查看现成开源方案，并明确选择 `React Flow + ELK`，撤回刚才偏自研的手写轨迹 UI 尝试。

本轮 UI 路线调整：

1. 全局状态图继续使用 `knowledge-graph-engine` 关系图谱，并把宿主侧默认 V2 graph 选择优先级改为 `project-checklist-current`，使全局关系图优先承载项目结构。
2. 局部工作轨迹图新增独立 webview bundle `vscode-extension/src/webviews/localWorkTrajectory.tsx`。
3. 该 bundle 使用 `@xyflow/react` 渲染节点/边，用 `elkjs` 计算单线轨迹布局。
4. 宿主只负责读取 `.codex/progress-graph/local-work-trajectory.json`、coerce 为 `ProgressGraphPreviewLocalWorkTrajectory`、注入 `pgHostLocalWorkTrajectoryPayload`，并挂载 React Flow JS/CSS bundle。
5. 当前仍只支持单线；多线、动态开线、指导上下文可视化和跨线关系样式留给后续切片。
6. 此处只记录图形展示路线，不扩展为 agent 集群或真实并行调度设计。

当前 focused validation：

1. 宿主 `npm run build` 通过。
2. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js` 通过，`6 passed`。
3. 后端 `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过，`3 passed`。
## 2026-06-04 lane-first layout revision

用户对当前蛇形折行单线提出反馈：这种展示方式不符合后续多线要求。结论如下：

1. 局部工作轨迹图必须采用 lane-first 展示语义。
2. 同一条工作线无论多长，都应保持在同一水平 lane 上推进，不应因为长度自动折成多行。
3. 图中的多行应保留给多条工作线；也就是说，纵向分层表达 lane 分离，而不是表达同一 lane 的折返阅读路径。
4. 长单线的可读性通过横向 pan、zoom、minimap、当前视口定位和后续可能的时间窗口/聚合来解决，不通过蛇形折行解决。
5. 事件顺序沿 x 轴从左到右推进；lane 标签固定在左侧语义区，作为该行上下文边界的短标签。
6. 未来动态开新线时，新 lane 可以从触发事件附近的 x 坐标开始，但仍应占用独立 y 轴 lane；这与单线折行是不同语义。
7. 跨线依赖、等待、合流等关系可以用少量跨 lane edge 表达，但不应把局部图退化为自由关系图谱。

## 2026-06-04 单线生命周期闭环

本轮补齐了单线后端闭环，使局部轨迹不再只能由 checkpoint todo 被动投影：

1. `tools/progress_graph/trajectory.py` 新增 `start_single_line_trajectory(...)`，用于创建初始 `lane:main` 和第一个 `in_progress` 节点。
2. 新增 `append_single_line_event(...)`，用于在同一工作线上追加后续节点，并自动补 `sequence` 关系。
3. 新增 `advance_single_line_event(...)`，用于把当前活动节点推进为 `completed`，并默认激活下一个 `pending` 节点。
4. 新增 `write_local_work_trajectory_artifact(...)`，用于 refresh artifact 生成：若当前 artifact 已由单线生命周期拥有，则刷新时保留显式推进状态；否则写入持久空 lifecycle 状态，避免重新回填 checkpoint todo 投影。
5. `vscode-extension/src/views/progressGraphArtifacts.ts` 已改用该 artifact writer，避免用户手动推进后的轨迹在 `Refresh Preview` 时被 checkpoint 投影覆盖。
6. 专用测试工作区 `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test` 只作为手动验证目标；自动测试默认不再写入该真实工作区。

仍然不在本轮处理：

1. 不支持动态开新线。
2. 不支持指导上下文可视化。
3. 不支持真实调度器或 agent runtime 绑定。
4. 不支持多线节点验收协议。

当前 focused validation：

1. `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过，`8 passed, 1 skipped`。
2. 宿主 `npm run build` 通过。
3. 宿主 `node --test dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` 通过，`11 passed`。

## 2026-06-04 单线命令与 UI 绑定（已废弃的历史实现）

本段记录一版已被后续 `agent-owned lifecycle mutation` 修正取代的历史实现。该方案曾把后端闭环暴露给 VS Code 命令面板和 progress graph preview，但它不再代表当前产品语义：

1. 新增宿主侧调用器 `vscode-extension/src/views/progressGraphTrajectoryActions.ts`，统一执行 `start`、`append`、`advance` 三类本地工作轨迹动作。
2. `ProgressGraphPreviewPanel` 新增 `startLocalWorkTrajectory(...)`、`appendLocalWorkTrajectoryEvent(...)`、`advanceLocalWorkTrajectoryEvent(...)`，并把 webview message 路由到同一套 action runner。
3. `package.json` 新增命令：
   - `docBasedCoding.startLocalWorkTrajectory`
   - `docBasedCoding.appendLocalWorkTrajectoryEvent`
   - `docBasedCoding.advanceLocalWorkTrajectoryEvent`
4. progress graph preview 的 Local Work Trajectory 区域新增轻量工具条：`Start`、`Append`、`Advance`。
5. 工具条按钮只发送 webview message；真正输入、Python 调用、错误处理和刷新都由扩展宿主统一完成。
6. `Start` 会询问 lane 短标签和第一个节点标题；`Append` 会询问节点标题与节点类型；`Advance` 直接推进当前活动节点。
7. 该绑定仍只支持单线，不支持开线、多线验收、指导上下文可视化或 runtime 调度接入。
8. `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test` 的真实写入 smoke 已改为环境变量 opt-in，避免自动测试污染手动测试状态。

当前 focused validation：

1. 宿主 `npm run build` 通过。
2. 宿主 `node --test dist/test/extensionManifest.test.js dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` 通过，`13 passed`。
3. 后端 `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过，`8 passed, 1 skipped`。

废弃原因：

1. `start`、`append`、`advance` 以及未来的 `merge`、开线、合流等轨迹突变不应由用户手动维护。
2. Local Work Trajectory UI 的职责应收束为展示和阅读，不应成为人工编辑器。
3. agent / tool / runtime 才是轨迹事件的拥有者；用户通过任务对话驱动工作，而不是通过按钮维护轨迹。
4. 当前代码已移除 `vscode-extension/src/views/progressGraphTrajectoryActions.ts`，`ProgressGraphPreviewPanel` 也不再持有人工 `showInputBox` / `showQuickPick` 版 mutation runner。

## 2026-06-04 单线活跃节点 UI 映射

本轮在单线命令/UI 绑定基础上补齐当前活动节点的可视映射：

1. `localWorkTrajectory.tsx` 在 lane-first layout 中寻找第一枚 `status === "in_progress"` 的事件，记录为 `activeEventId`。
2. 短线仍保持整图 fit；长线不再默认停留在起点，而是把视口聚焦到当前活动事件附近。
3. 当前活动事件节点增加蓝色强调、轻量阴影与 `pg-lwt-node-active` class；minimap 同步以蓝色显示该节点。
4. 该映射只表达“当前单线正在推进的节点”，不引入多线开设、指导上下文可视化、真实调度器或 agent runtime 绑定。

当前 focused validation：

1. 宿主 `npm run build` 通过。
2. 宿主 `node --test dist/test/extensionManifest.test.js dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` 通过，`13 passed`。
3. 后端 `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过，`8 passed, 1 skipped`。

## 2026-06-04 持久净空语义修正

本轮修正了“净空测试工作区 local map”的语义：

1. 删除 `local-work-trajectory.json` 并不是持久净空；refresh 会在文件缺失时重新生成 checkpoint todo 投影，导致旧的 100 节点链再次出现。
2. 新增 `clear_single_line_trajectory(...)`，写入一个 lifecycle-owned empty artifact：`projection=single-lane-lifecycle`、`lane_mode=single`、`lifecycle_state=empty`，且 0 lane / 0 event / 0 relation。
3. `write_local_work_trajectory_artifact(...)` 现在在缺失或旧 checkpoint 投影状态下写入 empty lifecycle，而不是回退生成 checkpoint todo 轨迹。
4. `localWorkTrajectory.tsx` 对 empty lifecycle 显示明确空状态，提示 agent 会在开始被跟踪任务时创建第一条 lane 与第一个 active event。
5. `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test` 已写入持久空 local map；refresh 后仍保持 0 lane / 0 event。
6. 真实 `dbc-test` 写入 smoke 测试改为 `DBC_PROGRESS_GRAPH_SMOKE_REAL_WORKSPACE=1` 时才执行，默认验证不再污染手动测试状态。

当前 focused validation：

1. 后端 `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过，`8 passed, 1 skipped`。
2. 宿主 `npm run build` 通过。
3. 宿主 `node --test dist/test/extensionManifest.test.js dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` 通过，`13 passed`。

## 2026-06-04 agent-owned lifecycle mutation 修正

用户进一步澄清：local trajectory 的 `start`、`append`、`merge` 等操作应由 agent 完成，而不是由人手动维护。

本轮据此修正入口语义：

1. Local Work Trajectory UI 只负责展示，不再在预览页提供 `Start` / `Append` / `Advance` 人工按钮。
2. VS Code command palette 不再贡献 `docBasedCoding.startLocalWorkTrajectory`、`docBasedCoding.appendLocalWorkTrajectoryEvent`、`docBasedCoding.advanceLocalWorkTrajectoryEvent` 这三个人工突变命令。
3. 底层 Python 单线 lifecycle API 保留为 agent/tool/runtime 可调用设施；预览面板不再持有人工 action runner。
4. 插件内 AI Chat tool loop 新增 `localTrajectory` 工具，允许 agent 在任务开始时 `start`，在规划/观察到里程碑时 `append`，在当前节点完成时 `advance`。
5. AI Chat system prompt 明确：workspace 内容仍属于 read-only slice，但 `localTrajectory` 是用于任务跟踪元数据写入的显式例外，agent 不应要求用户手动点击轨迹按钮。
6. `localTrajectory` 工具成功后，若 Progress Graph Preview 已打开，宿主会从磁盘静默重载一次预览，使 agent 写入的 local trajectory 尽快映射到图面。
7. 当前后端仍只支持单线 `start` / `append` / `advance`；`merge`、开新线、多线验收和指导上下文可视化仍属于后续切片，不在本轮伪实现。

当前 focused validation：

1. 后端 `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过，`8 passed, 1 skipped`。
2. 宿主 `npm run build` 通过。
3. 宿主 `node --test dist/test/aiChatToolLoop.test.js dist/test/extensionManifest.test.js dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` 通过，`18 passed`。

## 2026-06-04 Codex MCP localTrajectory 接入

用户进一步要求“补 MCP，一致用 localTrajectory”。本轮将 agent-owned lifecycle mutation 从 VS Code extension 内部 AI Chat tool loop 补齐到 Codex 可见的 MCP 工具面：

1. MCP server 现在注册对外工具名 `localTrajectory`。
2. `src/mcp/tools.py` 新增 `GovernanceTools.local_trajectory(...)`，作为 Python 内部 snake_case wrapper；对外协议、错误信息与文档统一使用 `localTrajectory`。
3. MCP `localTrajectory` 当前支持 `action=start|append|advance`，并复用现有 `start_single_line_trajectory(...)`、`append_single_line_event(...)`、`advance_single_line_event(...)`。
4. `eventKind` 显式限制为当前 `TrajectoryEventKind` 集合，避免 Codex 侧写入 UI 无法解释的事件类型。
5. 这不是 skill 注册面：skill 可用于后续策略说明，但真实轨迹突变能力必须来自运行时/MCP。
6. `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test\.vscode\mcp.json` 已修正为 `--project C:\Users\16329\OneDrive\Desktop\tmp\dbc-test`，避免把测试轨迹写回旧 `tmp\test`。
7. `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test\AGENTS.md` 已同步测试工作区地址，并明确任务型工作应由 agent 通过 MCP `localTrajectory` 维护轨迹。

当前 focused validation：

1. `python -m pytest tests/test_mcp_tools.py tests/test_progress_graph_trajectory.py -q` 通过，`62 passed, 1 skipped`。
2. 真实 `dbc-test` MCP handler smoke 通过：`tools/list` 可见 `localTrajectory`，`tools/call localTrajectory start` 能写入 `.codex/progress-graph/local-work-trajectory.json`。
3. smoke 后已调用 `clear_single_line_trajectory(...)` 将 `dbc-test` 恢复为 durable empty lifecycle，后续手动测试仍从空 local map 开始。

## 2026-06-05 Codex MCP 注册面诊断

用户反馈测试端 agent 仍看不到 `localTrajectory`。诊断结论如下：

1. 这不是 `localTrajectory` server 声明缺失；真实 stdio MCP client 握手已验证 `tools/list` 返回 18 个工具，包含 `localTrajectory`。
2. 原因是测试工作区此前只有 `.vscode/mcp.json`，该文件服务于 VS Code / Copilot Chat 注册面，不会让 Codex IDE 插件或 Codex CLI agent 自动获得 MCP 工具。
3. Codex 的实际注册面应是 `codex mcp add ...` 写入的 Codex config，或等价的 Codex config TOML；这与 `docs/codex-entry-contract.md` 和 `docs/installation-guide.md` 的边界一致。对于 VS Code Codex 插件，优先保证测试工作区存在项目级 `.codex/config.toml`，而不是只刷新 `.codex/progress-graph` 数据产物。
4. 当前已执行：
   `codex mcp add doc-based-coding -- "E:\workspace\tool develop\vibe coding facilities\doc based coding\.venv-release-test\Scripts\python.exe" -m src.mcp.server --project "C:\Users\16329\OneDrive\Desktop\tmp\dbc-test"`
5. `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test\.codex\config.toml` 已新增项目级 MCP server 配置，指向同一 `src.mcp.server --project C:\Users\16329\OneDrive\Desktop\tmp\dbc-test`。
6. `codex mcp list` 现在可见 MCP server `doc-based-coding`，状态为 `enabled`，命令指向测试工作区，并带有源码仓库 `cwd`。
7. 已用 `mcp.ClientSession + stdio_client` 对同一启动命令做真实握手验证：`has_localTrajectory=true`。
8. 既有已打开的 Codex agent 会话通常不会热加载刚新增的 MCP server；测试端应重启/新开 Codex 会话后再验证工具暴露。

当前 focused validation：

1. `codex mcp list` 可见 `doc-based-coding`。
2. `codex mcp get doc-based-coding` 显示 command/args 指向 `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test`，`cwd` 指向源码仓库。
3. Python MCP client stdio 握手返回 `tool_count=18`、`has_localTrajectory=true`。

## 2026-06-05 落地工作型 agent 轨迹闭环提示

用户在测试后确认 `localTrajectory` 工具暴露已通过，但真实测试工作区中出现了一个使用层缺口：agent 已记录 “Validated Luogu P1005 solution”，但该验证节点仍停留在 `pending`，当前活动节点仍是前一个 decision 节点。这说明工具链已经工作，但落地执行型 agent 的通用提示需要明确“验证/交付后继续推进轨迹到闭合态”。

本轮将该要求落到通用提示面，而不是只写入测试工作区：

1. VS Code 内部 AI Chat tool loop system prompt 新增规则：验证或交付完成后，应继续调用 `localTrajectory advance`，直到已完成的 validation/delivery 里程碑不再停留在 `pending` 或 `in_progress`。
2. `AiChatTools` 的 `localTrajectory` 工具描述同步补充同一规则。
3. MCP server 对外 tool description 同步补充同一规则，使 Codex MCP 工具发现面也能携带该行为预期。
4. `InstructionsGenerator` 新增 `Work Agent Local Trajectory` 静态段落，生成到 Codex `AGENTS.md` / 通用 instructions / Copilot instructions 中，作为落地工作型 agent 的通用提示词。
5. 本轮只修改提示词和工具描述，不改变 `start` / `append` / `advance` 状态机语义。

当前 focused validation：

1. `python -m pytest tests/test_instructions_generator.py tests/test_mcp_tools.py -q` 通过，`85 passed`。
2. `npm run build` 通过。
3. `node --test dist/test/aiChatToolLoop.test.js dist/test/aiChatViewIntegration.test.js` 通过，`7 passed`。

## 2026-06-05 单线 lifecycle 状态动作扩展

用户要求“按照单线的模式，开展剩余功能的展开”，本轮自行收窄为单线生命周期的状态控制补齐，而不是提前进入多线、开线、合流或指导上下文可视化。

本轮选择该范围的原因：

1. 当前真实测试已经证明 `start` / `append` / `advance` 可以跑通，但落地工作型 agent 在真实任务中仍缺少“更新当前节点、等待/阻塞、恢复、关闭整条线”的表达能力。
2. 这些能力都可以在现有单线 JSON schema 内通过 `event.status`、`lane.status`、`summary` 和 `metadata` 表达，不需要改 UI 布局或多线模型。
3. `merge`、动态开新线、跨线依赖和指导上下文审查属于多线语义，本轮不伪实现。

新增能力：

1. Python lifecycle 新增：
   - `update_single_line_event(...)`
   - `block_single_line_event(...)`
   - `resume_single_line_event(...)`
   - `close_single_line_trajectory(...)`
2. `localTrajectory` action 扩展为：
   - `start`
   - `append`
   - `advance`
   - `update`
   - `block`
   - `wait`
   - `resume`
   - `close`
3. `wait` 复用单线阻塞设施，但写入 `waiting` event/lane 状态与 `waiting_reason`。
4. `close` 完成当前事件，并把仍未执行的 pending / blocked / waiting 后续事件归档为 `archived`，使单线 lane 进入 `done`。
5. VS Code 内部 AI Chat 工具、MCP server tool schema、MCP `GovernanceTools.local_trajectory(...)` 和 agent prompt 已同步新动作。

当前非目标：

1. 不增加多线。
2. 不实现 `merge`。
3. 不改变 React Flow / Local Work Trajectory UI 布局。
4. 不改变现有 JSON schema 版本。
5. 不自动替 agent 决定何时开新线或合流。

当前 focused validation：

1. `python -m pytest tests/test_progress_graph_trajectory.py tests/test_mcp_tools.py -q` 通过，`64 passed, 1 skipped`。
2. `npm run build` 通过。
3. `node --test dist/test/aiChatToolLoop.test.js dist/test/aiChatViewIntegration.test.js` 通过，`7 passed`。

## 2026-06-05 单线状态 UI 绑定与多线第一步扩张

用户要求“先自行回环测试完成后进行 UI 绑定，完成后按单线经验完成多线内容的一步扩张”。本轮按该顺序推进。

回环测试结论：

1. 临时工作区执行 `start -> append -> update -> wait -> resume -> advance -> close`，最终 lane 状态为 `done`，事件引用与 sequence 关系无 invariant 错误。
2. 多线临时回环执行 `start -> addLane -> append(laneId) -> wait/resume/close(second lane) -> advance/close(main lane)`，最终 `lane_mode=multi`，两条 lane 均为 `done`，关系包含 `sequence` 与 `proposes_new_line`，无 invariant 错误。

UI 绑定：

1. Local Work Trajectory React Flow 节点现在显式映射 `waiting`、`blocked`、`done`、`completed`、`archived` 状态。
2. Lane 节点增加 `data-pg-lane-status` 与状态化背景色。
3. Event 节点增加状态化 class 与背景/边框；`waiting` 使用等待色，`archived` 降低视觉权重。
4. 当没有 `in_progress` 节点时，视图优先聚焦 `blocked` / `waiting` / `pending`，再退到已完成或归档节点，避免关闭后视口无意义回到起点。
5. Minimap 颜色同步区分 active、blocked、waiting、done/completed、archived。

多线第一步扩张：

1. 新增 `add_local_work_lane(...)`，只负责在现有 lifecycle artifact 中新增一条 lane 和首个 active event。
2. `localTrajectory` 新增 action `addLane`。
3. `addLane` 可接收：
   - `laneLabel`
   - `firstEventTitle`
   - `eventKind`
   - `summary`
   - `laneId`
   - `sourceEventId`
4. `append` 新增 `laneId`，允许向指定 lane 追加后续节点。
5. 新 lane 与触发事件之间写入 `proposes_new_line` 关系；这只表示“从该事件展开新工作线”，不表示 merge、依赖或指导上下文批准。
6. lifecycle metadata 的 `lane_mode` 在新增 lane 后更新为 `multi`。

当前非目标：

1. 不实现 merge。
2. 不实现跨线 depends_on / waits_for 的 agent API。
3. 不实现指导上下文审查。
4. 不改变 React Flow lane-first 布局。
5. 不把多线解释为真实并行 agent；它仍只表示相对独立工作上下文。

当前 focused validation：

1. `python -m pytest tests/test_progress_graph_trajectory.py tests/test_mcp_tools.py -q` 通过，`66 passed, 1 skipped`。
2. `npm run build` 通过。
3. `node --test dist/test/localWorkTrajectory.test.js dist/test/aiChatToolLoop.test.js dist/test/aiChatViewIntegration.test.js` 通过，`9 passed`。
