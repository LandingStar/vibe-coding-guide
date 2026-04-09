# 项目总清单与状态板

**(Project Master Checklist & Status Board)**

## 1. 文档定位

本文件是本项目当前阶段的**总入口、工作清单、状态存档与交接板**。

它服务于以下场景：

- 在多次对话之间快速恢复上下文。
- 在不同助手/协作者之间转交项目。
- 在进入编码前，确认哪些设计已经拍板、哪些仍待补完。
- 在编码开始后，持续记录实现状态、测试状态与待办事项。

若后续信息与其他文档冲突，应优先结合：

1. 用户在最新对话中的明确决定。
2. 本文件中的“已确认决策”与“当前状态”。
3. 对应专题设计文档。
4. 当前 active handoff 与 `.codex/handoffs/history/` 中必要的历史交接记录。
5. `tmp.txt` 中仍有必要追溯的历史推演记录。

---

## 2. 当前快照

**快照日期：** `2026-04-06`

**项目阶段：** `MVP` 已完成验收；宿主分离与诊断阶段（旧 `M6`、`M7-A`）已完成；多调度扩展阶段（旧 `M7-B`、`M7-C`）已完成；`Phase 5` 同步恢复与重新附着加固阶段已完成；`Phase 6` 调度系统深化阶段已完成；`Phase 7` 时间轴高级调度切片阶段已完成；`Phase 8` 时间轴恢复自动化切片阶段已完成；`Phase 9` 时间轴延后调度切片阶段已完成；`Phase 10` 窗口授予最小切片阶段已完成；`Phase 11` 时间轴 foreign-actor 窗口授予切片阶段已完成；`Phase 12` 时间轴 immediate 插入切片阶段已完成；`Phase 13` 跨驱动恢复泛化切片阶段已完成；`Phase 14` 跨驱动确定性矩阵切片阶段已完成；`Phase 15` effect authoring surface seed 阶段已完成；`Phase 16` effect runtime hook profile 切片阶段已完成；`Phase 17` authoring documentation standard gate 阶段已完成；当前重新处于“下一执行阶段规划门”。

**当前现实状态：**

- 工作区中现已包含设计文档、项目级 agent 配置，以及 `M0` 核心骨架与 `M1` 首个垂直切片源码。
- 项目已按 Python 小写包名落地第一版物理目录：
  - `core`
  - `standard_components`
  - `server`
  - `client`
  - `tests`
- 项目运行目标版本已固定为 Python `3.12`。
- 项目根目录现已提供统一配置入口：`config.json`。
- 当前全局阶段口径以：`Global Phase Map and Current Position.md` 为准。
- 阶段索引现已整理到：`design docs/stages/`
- `MVP` 阶段文档现已归档到：`design docs/stages/mvp/`
- 宿主分离与诊断阶段文档现已归档到：`design docs/stages/host-separation-and-diagnostics/`
- 多调度扩展阶段文档现已归档到：`design docs/stages/multi-scheduler-expansion/`
- `Phase 5` 文档现已归档到：`design docs/stages/runtime-hardening/`
- `Phase 8` 文档现已归档到：`design docs/stages/runtime-hardening/`
- `Phase 13` 文档现已归档到：`design docs/stages/runtime-hardening/`
- `Phase 14` 文档现已归档到：`design docs/stages/verification-and-determinism/`
- `Phase 15` 文档现已归档到：`design docs/stages/authoring-surface/`
- `Phase 16` 文档现已归档到：`design docs/stages/authoring-surface/`
- `Phase 17` 文档现已归档到：`design docs/stages/authoring-surface/`
- `Phase 6` 文档现已归档到：`design docs/stages/timeline_T1/scheduling-deepening/`
- `Phase 7` 文档现已归档到：`design docs/stages/timeline_T1/scheduling-deepening/`
- `Phase 9` 文档现已归档到：`design docs/stages/timeline_T1/scheduling-deepening/`
- `Phase 10` 文档现已归档到：`design docs/stages/timeline_T1/scheduling-deepening/`
- `Phase 11` 文档现已归档到：`design docs/stages/timeline_T1/scheduling-deepening/`
- `Phase 12` 文档现已归档到：`design docs/stages/timeline_T1/scheduling-deepening/`
- post-MVP 至 `Phase 12` 的 timeline 主线文档现已统一整理到：`design docs/stages/timeline_T1/`
- 下一执行阶段规划文档现已归档到：`design docs/stages/planning-gate/`
- 跨阶段长期工具链文档现已归档到：`design docs/tooling/`
- 多会话交接协议文档现已归档到：`design docs/tooling/`
- 项目级 handoff 产物目录与项目专用 handoff-system 目录现已固定到：`.codex/handoffs/` 与 `.codex/handoff-system/`
- 当前工作区现已是一个 git 仓库。
- `M0` 骨架实现已包含：
  - `BaseCommand / BaseEvent`
  - `World / Entity`
  - `EventBus`
  - `Lifecycle / Window Service`
  - 最小 `classical turn` driver
  - `ServerHost / ClientHost`
  - `demo/basic_combat.py` 正式最小攻击链切片
  - 按业务分流的日志设施（`core / driver / host_server / host_client / test`）
  - `project_config.py / project_setup.py` 根级装配与配置读取
  - `make_runtime / make_server_host / make_client_host` 统一 bootstrap 入口
  - `make_basic_combat_runtime / make_basic_combat_server_host / make_basic_combat_client_host` demo 一键入口
  - `make_configured_runtime / make_configured_server_host / make_configured_client_host` 配置驱动入口
  - `bootstrap.default_slice` 已接入配置，支持默认 demo slice 选择
  - 测试级统一日志保留（根目录 `logs/tests/<timestamp>/<test-node>/`）
  - 超出保留次数的历史测试日志自动压缩到 `logs/tests/_archives/`
  - 命令拒绝与事件校验失败路径的告警日志
  - `event_validator` 已接入最小攻击链并覆盖拒绝路径
  - `tests/acceptance/test_m0_acceptance.py` 已覆盖 `M0` 文档的主要验收条件
  - `standard_components/drivers/classical_turn/projection.py` 客户端最小 turn/window 投影
  - `demo/session.py` 本地 `ServerHost + ClientHost` 会话封装
  - `demo/cli.py` 终端可运行 demo 壳与 `tbge-demo` 入口
  - `client/console_app.py` 正式控制台 client 入口与 `tbge-client-console`
  - `WINDOW_*` 生命周期已调整为事件执行时生效，服务端与客户端的窗口观测时序现已对齐
  - CLI 对非法目标与命令拒绝已具备失败安全提示，不再直接崩溃退出
  - `M1 / MVP` 首个垂直切片的装配、CLI 分支和配置化 host 投影回归
  - `M1` 控制台 client 行为参数已进入根级 `config.json`
  - `tests/acceptance/test_m1_acceptance.py` 已固定当前 `M1` 自动化验收边界
  - `M2` 首个效果 / 修饰器 / 监听器切片已包含：
    - `standard_components/attributes/service.py`
    - `standard_components/effects/controller.py`
    - `RALLY -> ATTACK_UP` 修饰器链
    - `POISON` 基于 `TURN_END` 的监听器伤害链
    - `runtime.execution_role = authoritative / projection` 的最小执行画像区分
    - `import_state()` 后的效果监听器重建
    - `ServerHost.export_snapshot()` / `ClientHost.recover_from_snapshot()` / `LocalBattleSession.recover_client_from_server_snapshot()`
    - `tests/support/scenario_tools.py` 通用场景注入工具
    - `tests/acceptance/test_m2_acceptance.py` 自动化验收边界
  - `M3` 首个客户端预测 / 快照重播切片已包含：
    - `ClientHost.PendingCommandRecord`
    - `pending_command_buffer`
    - `ClientHost.predict_command()`
    - `ClientHost.recover_from_snapshot(..., replay_pending=True, rejected_command_id=...)`
    - `ClientHost.SyncRecoveryReport` 与 `last_sync_recovery_report`
    - `LocalBattleSession.reconcile_client_to_server_snapshot()`
    - `LocalBattleSession.commit_next_predicted_command()`
    - `LocalBattleSession.SyncStatus` 与 `current_sync_status()`
    - 单条 pending command 上限
    - `make_basic_combat_predictive_client_host()` 与 `make_configured_predictive_client_host()`
    - 控制台 CLI 的 `predictive` 模式切换、`sync / resync` 命令与日志回写
    - `classical_turn` 基于 `binding_token` 的最小跨重建绑定校验
    - 快照导出前同步 driver projection，保证 projection-only client 在 `resync` 后仍可恢复当前 actor / window / token
    - `tests/acceptance/test_m3_acceptance.py` 自动化验收边界
    - predictive CLI 的 `sync / resync / rally -> next turn` 路径已通过手测
  - `M4` 首切片现已包含：
    - `ClientHost` 多 pending buffer
    - `sent_to_server` 标记
    - replay / reject 失败后的向后截断策略
    - `LocalBattleSession` 的本地网络模拟队列与 `flush_network()`
    - predictive CLI 的 `--network-sim`、`net / queue / send / deliver / flush`
    - `tests/acceptance/test_m4_acceptance.py` 自动化验收边界
    - `M4 Manual Network Simulation Test Guide.md` 关键手测路径已通过
  - `M5` 首切片现已包含：
    - `server/stdio_app.py`
    - `transport/subprocess_proxy.py`
    - subprocess transport 下的 `basic_combat` authoritative / predictive / resync 主链
    - CLI 的 `--transport subprocess`
    - `tests/integration/test_subprocess_transport.py`
    - `tests/acceptance/test_m5_acceptance.py`
    - `tests/acceptance/test_mvp_acceptance.py`
    - `M5 Manual Physical Client-Server Test Guide.md`
    - `MVP Acceptance Guide.md`
  - `M6` 首切片现已包含：
    - `server/socket_app.py`
    - `transport/socket_proxy.py`
    - localhost `127.0.0.1` JSON-lines socket transport
    - `tbge-server-socket`
    - CLI 的 `--transport socket --attach-server --server-host --server-port`
    - CLI 的 `inject` / `desync`
    - `tests/support/socket_server.py`
    - `tests/integration/test_socket_transport.py`
    - `tests/acceptance/test_m6_acceptance.py`
    - `M6 Localhost Socket Transport and CLI Injection Slice.md`
    - `M6 Manual Localhost Socket Test Guide.md`
    - `M7 Transport Resilience and Timeline Entry Scope.md`
    - `Post-MVP Scope Guardrails and Next-Step Plan.md`
  - `M7-A` 首切片现已包含：
    - `transport/errors.py`
    - `SubprocessServerProxy.ping() / transport_report()`
    - `SocketServerProxy.ping() / transport_report()`
    - `ServerHost.ping() / transport_report()`
    - `LocalBattleSession.transport_status()`
    - `LocalBattleSession.ping_transport()`
    - CLI 的 `transport` / `ping`
    - `tests/acceptance/test_m7a_acceptance.py`
    - `M7-A Transport Resilience and Sync Diagnostics Slice.md`
  - `M7-B` 首切片现已包含：
    - `standard_components/drivers/timeline/driver.py`
    - `standard_components/drivers/timeline/projection.py`
    - `standard_components/drivers/projection_state.py`
    - `project_setup.make_timeline_driver()`
    - CLI 的 `--driver classical_turn|timeline`
    - `server/stdio_app.py` 与 `server/socket_app.py` 的 `--driver`
    - `transport/subprocess_proxy.py` 与 `transport/socket_proxy.py` 的 driver 透传
    - CLI 的 `inject ... time ...`
    - `tests/components/test_timeline_driver.py`
    - `tests/integration/test_timeline_projection.py`
    - `tests/acceptance/test_m7b_acceptance.py`
    - `M7-B Timeline Authoritative Slice.md`
    - `M7-B Manual Timeline Authoritative Test Guide.md`
  - `M7-C` 首切片现已包含：
    - Timeline predictive 装配
    - Timeline replay / resync
    - Timeline 下的 local network simulation
    - Timeline predictive 的 subprocess / socket smoke
    - `tests/integration/test_timeline_prediction.py`
    - `tests/acceptance/test_m7c_acceptance.py`
    - `M7-C Timeline Predictive and Replay Slice.md`
    - `M7-C Manual Timeline Predictive Test Guide.md`
  - `Phase 6` 首切片现已包含：
    - timeline committed `SPEED_CHANGED`
    - `standard_components/drivers/timeline/install_timeline_runtime_support()`
    - `TimelineDriver.apply_speed_changed()`
    - `HASTE`
    - CLI 的 `haste`
    - CLI 的 `inject ... speed ...`
    - `status` 的 `SPD`
    - `tests/acceptance/test_phase6_acceptance.py`
    - `Phase 6 Timeline Dynamic Speed Slice.md`
    - `Phase 6 Manual Timeline Dynamic Speed Test Guide.md`
  - `Phase 7` 首切片现已包含：
    - `ScheduleAdjustEvent`
    - `ADVANCE + NORMALIZED_PERCENT`
    - `standard_components/drivers/timeline/apply_schedule_adjust()`
    - 超量距离优先的 due actor 选择
    - `PULL`
    - CLI 的 `pull`
    - timeline `status` 的 `AV`
    - `tests/acceptance/test_phase7_acceptance.py`
    - `Phase 7 Timeline Advanced Scheduling Slice.md`
    - `Phase 7 Manual Timeline Advanced Scheduling Test Guide.md`
  - `Phase 8` 首切片现已包含：
    - `transport.auto_recover_enabled / auto_recover_max_attempts`
    - `SocketServerProxy.reconnect(force=True)`
    - `LocalBattleSession.RecoveryAutomationStatus`
    - `LocalBattleSession.recover_transport()`
    - `timeline predictive socket` 命令提交路径上的自动恢复重试
    - `timeline predictive socket` 的 `resync` 自动恢复
    - CLI 的 `recover`
    - `transport` 中的 `auto_recover / last_recovery`
    - `tests/acceptance/test_phase8_acceptance.py`
    - `Phase 8 Timeline Recovery Automation Slice.md`
    - `Phase 8 Manual Timeline Recovery Automation Test Guide.md`
  - `Phase 9` 首切片现已包含：
    - `DELAY + NORMALIZED_PERCENT`
    - `demo/basic_combat.py` 中的 `DELAY`
    - `demo/session.py` 中的 `make_delay() / submit_delay() / predict_delay()`
    - CLI 的 `delay`
    - `tests/acceptance/test_phase9_acceptance.py`
    - `Phase 9 Timeline Delay Slice.md`
    - `Phase 9 Manual Timeline Delay Test Guide.md`
  - `Phase 10` 首切片现已包含：
    - `WINDOW_GRANT`
    - `ENTITY_COMMAND_WINDOW + AFTER_CURRENT`
    - self grant only
    - `demo/basic_combat.py` 中的 `EXTRA`
    - `demo/session.py` 中的 `make_extra() / submit_extra() / predict_extra()`
    - CLI 的 `extra`
    - stale `TURN_END` 的 same-actor granted window 防护
    - granted window 的 timeline 序列化 / 快照恢复回归
    - `tests/acceptance/test_phase10_acceptance.py`
    - `Phase 10 Window Grant Minimal Slice.md`
    - `Phase 10 Manual Window Grant Test Guide.md`
  - `Phase 11` 首切片现已包含：
    - foreign-actor `WINDOW_GRANT(AFTER_CURRENT)`
    - `demo/basic_combat.py` 中的 `GRANT`
    - `demo/session.py` 中的 `make_grant() / submit_grant() / predict_grant()`
    - CLI 的 `grant`
    - foreign grant 的 hidden future slot 暂存、恢复与 speed-rescale
    - stale `TURN_END` 对 foreign granted window 的 same-window 防护
    - foreign granted window 的 timeline 序列化 / 快照恢复回归
    - `tests/acceptance/test_phase11_acceptance.py`
    - `Phase 11 Timeline Foreign-Actor Window Grant Slice.md`
    - `Phase 11 Manual Foreign-Actor Window Grant Test Guide.md`
  - `Phase 12` 首切片现已包含：
    - foreign-actor `WINDOW_GRANT(IMMEDIATE)`
    - `demo/basic_combat.py` 中的 `IMMEDIATE`
    - `demo/session.py` 中的 `make_immediate() / submit_immediate() / predict_immediate()`
    - CLI 的 `immediate`
    - immediate insert 的 suspend / resume 恢复
    - `core/world/dto.py` 的深拷贝修正，避免 predictive client 写脏 authority projection
    - immediate 链路的序列化 / 快照恢复回归
    - `tests/acceptance/test_phase12_acceptance.py`
    - `Phase 12 Timeline Immediate Insert Minimal Slice.md`
    - `Phase 12 Manual Timeline Immediate Insert Test Guide.md`
  - `Phase 13` 首切片现已包含：
    - predictive socket recovery 的最小 cross-driver 泛化
    - `classical_turn` predictive socket 的 `resync` 自动恢复 smoke
    - `classical_turn` predictive socket 的命令提交自动恢复 smoke
    - cross-driver 的非对称 scheduler-state 注入恢复回归
    - CLI `transport / sync / recover` 的 driver-neutral 资格与状态显示
    - `tests/acceptance/test_phase13_acceptance.py`
    - `Phase 13 Cross-Driver Recovery Generalization Slice.md`
    - `Phase 13 Manual Cross-Driver Recovery Test Guide.md`
  - `Phase 14` 首切片现已包含：
    - `tools/verification_platform/matrix.py`
    - `tools/verification_platform/cli.py`
    - `tbge-verify-matrix` 脚本入口定义
    - `authoritative_basic_attack / predictive_rally_commit / predictive_disconnect_recover_rally` 三类 canonical 场景
    - authority/client 的稳定状态摘要对齐检查
    - cross-driver / cross-transport 的最小 determinism matrix
    - `tests/integration/test_verification_matrix.py`
    - `tests/acceptance/test_phase14_acceptance.py`
    - `Phase 14 Cross-Driver Determinism Matrix Slice.md`
    - `Phase 14 Manual Determinism Matrix Test Guide.md`
  - `Phase 15` 首切片现已包含：
    - `standard_components/effects/models.py`
    - `standard_components/effects/authoring.py`
    - `EffectController.registry`
    - `EffectController.build_effect(...)`
    - `APPLY_EFFECT` 的通用构建入口
    - CLI 的 `effects`
    - `tests/components/test_effect_authoring.py`
    - `tests/acceptance/test_phase15_acceptance.py`
    - `Phase 15 Effect Authoring Surface Seed.md`
    - `Phase 15 Manual Effect Authoring Surface Test Guide.md`
  - `Phase 16` 首切片现已包含：
    - `RuntimeHookProfile`
    - `EffectDefinition.runtime_hook_profile_key`
    - `EffectRegistry` 的 runtime hook profile 注册与查询
    - `TURN_END_DECAY`
    - `TURN_END_TICK_DAMAGE_AND_DECAY`
    - `POISON` 的 profile 化 runtime hook 安装
    - CLI `effects` 的 runtime hook profile 展示
    - `tests/acceptance/test_phase16_acceptance.py`
    - `Phase 16 Effect Runtime Hook Profile Slice.md`
    - `Phase 16 Manual Effect Runtime Hook Profile Test Guide.md`
  - 非对称注入回归现已固定覆盖：
    - `Phase 6` 的速度变化链
    - `Phase 7` 的 `pull`
    - `Phase 8` 的 timeline recovery
    - `Phase 9` 的 `delay`
    - `Phase 10` 的 granted window 恢复覆盖
    - `Phase 11` 的 foreign granted hidden future slot 恢复覆盖
    - `Phase 13` 的 cross-driver predictive socket scheduler-state 恢复覆盖
  - cross-driver determinism matrix 现已固定覆盖：
    - `authoritative_basic_attack`
    - `predictive_rally_commit`
    - `predictive_disconnect_recover_rally`
  - 跨阶段验证门现已固定到：
    - `design docs/Verification Gate and Phase Acceptance Workflow.md`
    - `.codex/agents/verification-reviewer.md`
- CLI 命令参考现已固定到：
    - `demo/command_reference.py`
    - `design docs/CLI Command Reference.md`
    - `help`、`help <command>`、`help all` 已与之对齐，并由回归测试约束后续维护
- 作者化使用文档现已固定到：
    - `design docs/tooling/Authoring Documentation Standard.md`
    - `design docs/tooling/Effect Authoring Surface Usage Guide.md`
    - `design docs/tooling/Effect Runtime Hook Profile Usage Guide.md`
- 当前自动化验证状态：
  - `python3.12 -m pytest -q`
  - `301 passed`
  - `python3.12 -m compileall core standard_components server client demo transport tests tools project_config.py project_setup.py`
  - `通过`
- 当前本机已安装 `python3.12`（`3.12.13`），项目 `.venv` 已切换为 Python `3.12.13`。
- 当前系统默认 `python3` 仍为 Ubuntu `25.10` 自带的 Python `3.13.7`，本轮未覆盖系统默认解释器，只完成了 `python3.12` 的安装与项目环境迁移。

**一句话判断：**

项目已经完成 `MVP`、宿主分离与诊断、多调度扩展、`Phase 5`、`Phase 6`、`Phase 7`、`Phase 8`、`Phase 9`、`Phase 10`、`Phase 11`、`Phase 12`、`Phase 13`、`Phase 14`、`Phase 15`、`Phase 16` 与 `Phase 17` 的当前验收线。当前项目不仅具备最小物理 C/S 切片，而且已经能以独立 server/client 进程通过 `127.0.0.1` 端口通信，并支持 CLI 手动注入错位、恢复、timeline 的动态速度变化、主动调度切片（`ADVANCE / DELAY`），以及 timeline 的 self / foreign granted window 与 foreign immediate insert 切片、predictive socket 自动恢复、最小 cross-driver 恢复泛化验证、可运行的 determinism matrix 工具入口，以及 effect authoring surface 的最小 catalog / registry / build / runtime hook profile 入口与面向使用者的作者化文档标准。

---

## 3. 已确认决策

以下内容视为当前已拍板的高优先级设计前提，后续工作默认遵守：

- 从项目第一步起采用**物理隔离**的客户端/服务端架构，而不是单进程内的伪分层。
- `Core` 逻辑需要被前后端**双端复用**。
- 引擎采用**微内核架构**：`Core` 只保留容器、总线、接口与最小流程控制；复杂机制通过标准组件或自定义组件注入。
- 核心逻辑以**单线程、同步、确定性**为底线，不依赖多线程/多进程来推进核心结算。
- 引擎必须支持至少两类行动权系统：
  - AV 时间轴系统。
  - 经典严格回合制驱动。
- 引擎采用**事件驱动**，事件拥有三阶段生命周期：
  - `OnBefore`
  - `OnExecute`
  - `OnAfter`
- Buff 既是属性修饰器提供者，也是事件监听器。
- 前后端网络语义严格区分：
  - `Command` 表示玩家意图，客户端发往服务端。
  - `Event` 表示客观事实，服务端发往客户端。
- 引擎保留**弹性校验模式**：
  - 严格服务端权威。
  - 客户端预测与本地校验。
- 事件在内存中允许形成因果树，在网络上传输时拍扁为一维数组，并通过 `parent_event_id` 重建树结构。
- TOCTOU 校验在事件真正执行前进行，且校验器采用 `(event, world)` 通用签名。
- 高级时序规则不应污染 `Core`，例如《游戏王》式 LIFO 连锁，应通过拦截器/标准组件实现。

---

## 4. 文档结构与完成度

| 模块 | 文件 | 状态 | 说明 |
| --- | --- | --- | --- |
| 总纲 | `description.md` | `archived` | 最早期背景与愿景草案，保留历史价值，但不是当前主规范。 |
| 总纲 | `Framework.md` | `settled` | 提供总览，并已完成当前阶段子文档入口整理。 |
| 宏观架构 | `Engine Macro-Architecture.md` | `settled` | 微内核与依赖注入的最高设计纲领。 |
| 时间轴 | `timeline system.md` | `settled` | AV 模型、主循环、速度变化、拉条/插队已经较完整。 |
| 时间轴补充 | `Speed Clamping.md` | `settled` | 速度小于等于 0 的冻结处理。 |
| 时间轴补充 | `Tie-breaker Protocol.md` | `settled` | 确定性撞线排序规则。 |
| 替代驱动 | `classical turn driver.md` | `settled` | 严格回合制组件与其边界问题。 |
| 实体与属性 | `attributes and buffs.md` | `settled` | 主体结构清楚，`[2-A]` 与 `[2-B]` 均已由子文档补完。 |
| 属性求值子文档 | `Modifier Stacking and Attribute Evaluation Profiles.md` | `settled` | 正式定义了 Modifier 管线元件、叠层合同、官方默认 profile 与注册机制。 |
| 监听器调度子文档 | `Listener Priority Resolution and Phase Profiles.md` | `settled` | 正式定义了 Listener 的 lane、band、phase scheduler 与默认 phase profile。 |
| 通信总览 | `base event function and communication system.md` | `settled` | 网络与同步主线完整，已挂接 3-B 与 3-C。 |
| 协议主文档 | `Command and Event Core Structure and Serialization.md` | `settled` | `BaseCommand / BaseEvent` 主文档，文件名与正文主题现已对齐。 |
| TOCTOU 子文档 | `detail in TOCTOU resolution.md` | `settled` | 执行前校验与善后策略已成型。 |
| 校验 API | `Standard Validation Component and API Syntax Sugar.md` | `settled` | 内容与编号现已对齐，可作为 3-A-2 使用。 |
| 事件总线主文档 | `Event Bus Pipeline and Context Flattening Algorithm.md` | `settled` | 上下文栈、拍扁、DFS、批处理原则已成型。 |
| 高级时序 | `LIFO Chain via Interceptor.md` | `settled` | 作为标准扩展组件的连锁机制已定方向。 |
| 状态快照 | `State Snapshot and World Overwrite Protocol.md` | `settled` | 3-C 已落文，明确了 ID 寻址、世界重建与静默快进基线。 |
| 窗口协议 | `Window Service and Lifecycle Control Protocol.md` | `settled` | 正式定义了 Lifecycle Control、Window Service、Focus 扩展拆分，以及窗口协议事件与 turn 投影边界。 |
| 调度度量协议 | `Scheduling Metric Change Protocol.md` | `settled` | 正式定义了属性管线向调度 driver 广播关键度量变化的最小模板。 |
| 调度操作协议 | `Scheduling Adjustment and Window Grant Protocol.md` | `settled` | 正式定义了顺位调整与窗口授予的两类调度操作模板。 |
| 验证门 | `Verification Gate and Phase Acceptance Workflow.md` | `settled` | 定义所有后续阶段共享的验收前验证流程与 reviewer 分工。 |
| 阶段总览 | `Global Phase Map and Current Position.md` | `settled` | 用新的全局阶段口径解释已完成工作、当前阶段与历史 `M*` 文档的阅读方式。 |
| 阶段索引 | `stages/README.md` | `settled` | 全局阶段目录入口。 |
| 索引 | `stages/mvp/README.md` | `settled` | `MVP` 阶段文档归档入口。 |
| 索引 | `stages/host-separation-and-diagnostics/README.md` | `settled` | 宿主分离与诊断阶段归档入口。 |
| 索引 | `stages/multi-scheduler-expansion/README.md` | `settled` | 多调度扩展阶段归档入口。 |
| 索引 | `stages/runtime-hardening/README.md` | `settled` | `Phase 5` 同步恢复与重新附着加固阶段归档入口。 |
| 索引 | `stages/verification-and-determinism/README.md` | `settled` | 验证平台雏形与确定性矩阵阶段归档入口。 |
| 索引 | `stages/scheduling-deepening/README.md` | `settled` | 旧的调度深化入口，现作为跳转页保留。 |
| 索引 | `stages/timeline_T1/scheduling-deepening/README.md` | `settled` | timeline 调度深化执行文档的新归档入口。 |
| 索引 | `stages/planning-gate/README.md` | `settled` | 下一执行阶段规划门入口。 |
| 索引 | `tooling/README.md` | `settled` | 跨阶段长期工具链文档入口，不参与阶段归档层级。 |
| 实现规划 | `stages/mvp/M0 Core Skeleton Scope and Reserved Interfaces.md` | `settled` | 正式定义了 M0 核心骨架范围、非目标与必须预留的未来接口。 |
| 实现规划 | `stages/mvp/M1 MVP Scope and First Vertical Slice.md` | `settled` | 正式定义了 M1 的当前范围、首个 vertical slice、当前非目标与验收条件。 |
| 手动验收 | `stages/mvp/M1 Manual Console Test Guide.md` | `settled` | 提供 M1 控制台 client 的正式手动测试入口、步骤与通过判定。 |
| 实现规划 | `stages/mvp/M2 Effects, Modifiers, and Listener Slice.md` | `settled` | 记录了当前已落地的 `RALLY / ATTACK_UP / POISON` 切片、执行画像边界与当前非目标。 |
| 验收指引 | `stages/mvp/M2 Acceptance and Scenario Injection Guide.md` | `settled` | 固定了 M2 当前通过标准、快照恢复入口与场景注入工具用法。 |
| 实现规划 | `stages/mvp/M3 Client Prediction and Snapshot Replay Slice.md` | `settled` | 固定了当前 predictive client、pending buffer、快照恢复、重播与 CLI 入口的首切片边界。 |
| 手动验收 | `stages/mvp/M3 Manual Predictive Console Test Guide.md` | `settled` | 固定了当前 predictive CLI 的手测路径、同步命令与通过判定。 |
| 实现规划 | `stages/mvp/M4 Multi-Command Prediction and Network Simulation Scope.md` | `settled` | 固定了下一阶段的多命令 pending、稳定 token 与本地网络模拟主线。 |
| 手动验收 | `stages/mvp/M4 Manual Network Simulation Test Guide.md` | `settled` | 固定了当前 M4 首切片的本地网络模拟控制台手测入口与通过判定。 |
| 实现规划 | `stages/mvp/M5 Transport Host and Physical Client-Server Slice.md` | `settled` | 固定了 M4 收口后的下一阶段：传输宿主、物理 C/S 首切片与 MVP 剩余工作主线。 |
| 手动验收 | `stages/mvp/M5 Manual Physical Client-Server Test Guide.md` | `settled` | 固定了当前 M5 subprocess transport 的控制台手测入口与通过判定。 |
| 验收总览 | `stages/mvp/MVP Acceptance Guide.md` | `settled` | 汇总当前 MVP 的自动化/手动验收依据与通过判定。 |
| 实现规划 | `stages/host-separation-and-diagnostics/M6 Post-MVP Transport Hardening and Timeline Scope.md` | `settled` | 记录 localhost socket transport 与 CLI 注入/错位测试切片；现归类到宿主分离与诊断阶段。 |
| 手动验收 | `stages/host-separation-and-diagnostics/M6 Manual Localhost Socket Test Guide.md` | `settled` | 固定了独立 server/client 通过 `127.0.0.1` 端口通信时的手测入口。 |
| 实现规划 | `stages/host-separation-and-diagnostics/M7-A Transport Resilience and Sync Diagnostics Slice.md` | `settled` | 记录 transport 诊断、ping 与 CLI 观测能力切片；现归类到宿主分离与诊断阶段。 |
| 实现规划 | `stages/multi-scheduler-expansion/M7-B Timeline Authoritative Slice.md` | `settled` | 记录 Timeline authoritative 首切片；现归类到多调度扩展阶段。 |
| 手动验收 | `stages/multi-scheduler-expansion/M7-B Manual Timeline Authoritative Test Guide.md` | `settled` | 固定了 Timeline authoritative 的本地与 socket 手测入口。 |
| 实现规划 | `stages/multi-scheduler-expansion/M7-C Timeline Predictive and Replay Slice.md` | `settled` | 记录 Timeline predictive / replay / resync 首切片；现归类到多调度扩展阶段。 |
| 手动验收 | `stages/multi-scheduler-expansion/M7-C Manual Timeline Predictive Test Guide.md` | `settled` | 固定了 Timeline predictive 的本地、network simulation 与 socket 手测入口。 |
| 实现规划 | `stages/timeline_T1/scheduling-deepening/Phase 6 Timeline Dynamic Speed Slice.md` | `settled` | 记录 timeline 动态速度变化切片、当前边界与验收依据。 |
| 手动验收 | `stages/timeline_T1/scheduling-deepening/Phase 6 Manual Timeline Dynamic Speed Test Guide.md` | `settled` | 固定了 authoritative / predictive / inject speed 的手测路径。 |
| 实现规划 | `stages/timeline_T1/scheduling-deepening/Phase 7 Timeline Advanced Scheduling Slice.md` | `settled` | 记录 timeline 首个主动调度操作切片、边界与验收依据。 |
| 手动验收 | `stages/timeline_T1/scheduling-deepening/Phase 7 Manual Timeline Advanced Scheduling Test Guide.md` | `settled` | 固定了 authoritative / predictive / subprocess 下 `pull` 的手测路径。 |
| 实现规划 | `stages/timeline_T1/scheduling-deepening/Phase 9 Timeline Delay Slice.md` | `settled` | 记录 timeline 对称延后调度切片、当前边界与验收依据。 |
| 手动验收 | `stages/timeline_T1/scheduling-deepening/Phase 9 Manual Timeline Delay Test Guide.md` | `settled` | 固定了 authoritative / predictive / subprocess 下 `delay` 的手测路径。 |
| 实现规划 | `stages/timeline_T1/scheduling-deepening/Phase 10 Window Grant Minimal Slice.md` | `settled` | 记录 timeline 最小窗口授予切片、当前边界与验收依据。 |
| 手动验收 | `stages/timeline_T1/scheduling-deepening/Phase 10 Manual Window Grant Test Guide.md` | `settled` | 固定了 authoritative / predictive / subprocess 下 `extra` 的手测路径。 |
| 实现规划 | `stages/timeline_T1/scheduling-deepening/Phase 11 Timeline Foreign-Actor Window Grant Slice.md` | `settled` | 记录 timeline foreign-actor granted window 切片、hidden future slot 恢复边界与验收依据。 |
| 手动验收 | `stages/timeline_T1/scheduling-deepening/Phase 11 Manual Foreign-Actor Window Grant Test Guide.md` | `settled` | 固定了 authoritative / predictive / subprocess 下 `grant` 的手测路径与显式观察点。 |
| 实现规划 | `stages/timeline_T1/scheduling-deepening/Phase 12 Timeline Immediate Insert Minimal Slice.md` | `settled` | 记录 timeline foreign-actor immediate insert 切片、suspend / resume 恢复边界与验收依据。 |
| 手动验收 | `stages/timeline_T1/scheduling-deepening/Phase 12 Manual Timeline Immediate Insert Test Guide.md` | `settled` | 固定了 authoritative / predictive / subprocess 下 `immediate` 的手测路径与显式观察点。 |
| 规划历史 | `stages/planning-gate/M7 Transport Resilience and Timeline Entry Scope.md` | `settled` | 保留从宿主分离阶段过渡到 Timeline 接入时的规划轨迹。 |
| 范围约束 | `stages/planning-gate/Post-MVP Scope Guardrails and Next-Step Plan.md` | `settled` | 保留旧的 post-MVP 范围约束与禁止事项，供下一阶段规划参考。 |
| 实现规划 | `stages/runtime-hardening/Phase 5 Sync Recovery and Re-attach Hardening.md` | `settled` | 记录 `Phase 5` 的目标、实现边界、已落地内容与验收依据。 |
| 手动验收 | `stages/runtime-hardening/Phase 5 Manual Recovery and Reconnect Test Guide.md` | `settled` | 固定了 `Phase 5` 的 socket 重连恢复与 subprocess 注入恢复手测路径。 |
| 实现规划 | `stages/runtime-hardening/Phase 8 Timeline Recovery Automation Slice.md` | `settled` | 记录 timeline predictive socket 自动恢复切片、当前边界与验收依据。 |
| 手动验收 | `stages/runtime-hardening/Phase 8 Manual Timeline Recovery Automation Test Guide.md` | `settled` | 固定了自动恢复命令提交流与手动 `recover` 的手测路径。 |
| 实现规划 | `stages/runtime-hardening/Phase 13 Cross-Driver Recovery Generalization Slice.md` | `settled` | 记录 predictive socket recovery 从 timeline 特例迈向最小 cross-driver 泛化的切片、边界与验收依据。 |
| 手动验收 | `stages/runtime-hardening/Phase 13 Manual Cross-Driver Recovery Test Guide.md` | `settled` | 固定了 classical_turn / timeline 两条 predictive socket 恢复手测路径与非对称注入观察点。 |
| 实现规划 | `stages/verification-and-determinism/Phase 14 Cross-Driver Determinism Matrix Slice.md` | `settled` | 记录最小 determinism matrix、稳定状态摘要与验证平台雏形首轮建设的边界与验收依据。 |
| 手动验收 | `stages/verification-and-determinism/Phase 14 Manual Determinism Matrix Test Guide.md` | `settled` | 固定了矩阵工具的手动运行入口、预期输出与观察重点。 |
| 阶段索引 | `stages/authoring-surface/README.md` | `settled` | 汇总作者化与承载面主线的执行文档。 |
| 实现规划 | `stages/authoring-surface/Phase 15 Effect Authoring Surface Seed.md` | `settled` | 记录 effect catalog、definition registry 与最小 authoring surface 的边界与验收依据。 |
| 手动验收 | `stages/authoring-surface/Phase 15 Manual Effect Authoring Surface Test Guide.md` | `settled` | 固定了 `effects`、`help effects` 与现有效果链的手测路径。 |
| 实现规划 | `stages/authoring-surface/Phase 16 Effect Runtime Hook Profile Slice.md` | `settled` | 记录 effect runtime hook profile、POISON 迁移与 CLI 观察面的边界与验收依据。 |
| 手动验收 | `stages/authoring-surface/Phase 16 Manual Effect Runtime Hook Profile Test Guide.md` | `settled` | 固定了 runtime hook profile 的手测路径与观察点。 |
| 实现规划 | `stages/authoring-surface/Phase 17 Authoring Documentation Standard Gate.md` | `settled` | 记录作者化文档标准、样例归一化与最小自动检查的边界与验收依据。 |
| 手动验收 | `stages/authoring-surface/Phase 17 Manual Authoring Documentation Standard Test Guide.md` | `settled` | 固定了文档检查、discovery surface 观察与针对性自动化入口。 |
| CLI 参考 | `CLI Command Reference.md` | `settled` | 与 `demo/command_reference.py` 同步，作为控制台命令帮助与文档的统一参考。 |
| 工具链标准 | `tooling/Authoring Documentation Standard.md` | `settled` | 固定作者化文档的长期放置位置、最小章节模板、完成定义与 discovery surface 同步边界。 |
| 工具链标准 | `tooling/Session Handoff Standard.md` | `settled` | 固定多会话 handoff 的类型、安全停点、core fields、接手流程与 `Other` 审查规则。 |
| 工具链标准 | `tooling/Session Handoff Conditional Blocks.md` | `settled` | 固定 handoff 的 conditional block 注册表、扩展规则与 `Other -> block` 晋升标准。 |
| 工具链标准 | `tooling/Verification Platform Seed and Tooling Standards.md` | `settled` | 记录验证平台雏形的长期身份、分层结构与与 skill / MCP / 独立工具的关系。 |
| 使用指南 | `tooling/Effect Authoring Surface Usage Guide.md` | `settled` | 面向使用者说明 effect definition / registry / build 的最小作者化入口。 |
| 使用指南 | `tooling/Effect Runtime Hook Profile Usage Guide.md` | `settled` | 面向使用者说明 runtime hook profile 的当前使用方式与边界。 |
| 候选 backlog | `stages/planning-gate/M8 Advanced Scheduling and Recovery Backlog.md` | `settled` | 记录下一执行阶段的候选主线，不代表当前已启动工作。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 7 Candidates.md` | `settled` | 记录引擎层面的剩余工作图与下一阶段候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 8 Candidates.md` | `settled` | 记录 `Phase 7` 收口后的更广剩余工作图与 `Phase 8` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 9 Candidates.md` | `settled` | 记录 `Phase 8` 收口后的更广剩余工作图与 `Phase 9` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 10 Candidates.md` | `settled` | 记录 `Phase 9` 收口后的更广剩余工作图与 `Phase 10` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 11 Candidates.md` | `settled` | 记录 `Phase 10` 收口后的更广剩余工作图与 `Phase 11` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 12 Candidates.md` | `settled` | 记录 `Phase 11` 收口后的更广剩余工作图与 `Phase 12` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 13 Candidates.md` | `settled` | 记录 `Phase 12` 收口后的更广剩余工作图与 `Phase 13` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 14 Candidates.md` | `settled` | 记录 `Phase 13` 收口后的更广剩余工作图与 `Phase 14` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 15 Candidates.md` | `settled` | 记录 `Phase 14` 收口后的更广剩余工作图与 `Phase 15` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 16 Candidates.md` | `settled` | 记录 `Phase 15` 收口后的更广剩余工作图与 `Phase 16` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 17 Candidates.md` | `settled` | 记录 `Phase 16` 收口后的更广剩余工作图与 `Phase 17` 候选。 |
| 剩余工作图 | `stages/planning-gate/Engine Remaining Work Map and Phase 18 Candidates.md` | `settled` | 记录 `Phase 17` 收口后的更广剩余工作图与 `Phase 18` 候选。 |
| 阶段索引 | `stages/timeline_T1/README.md` | `settled` | 汇总 post-MVP 结束到 `Phase 12` 的 timeline 主线执行文档，不改动原始阶段正文。 |
| 历史对话 | `tmp.txt` | `reference` | 设计演化过程与部分未正式固化的细节来源。 |

**状态词说明：**

- `settled`：主架构已经明确，可据此继续细化或实现。
- `partial`：主方向明确，但仍存在关键留空或组织问题。
- `archived`：保留历史背景，不作为当前规范中心。
- `reference`：提供推演上下文，不直接作为主规范。

---

## 5. 当前缺口清单

### P0：编码前建议先补齐

当前无额外 `P0` 文档缺口。

已完成的关键设计补完包括：

- `[2-A]` 修饰器叠加算法与属性求值 profile
- `[2-B]` 同一生命周期内的监听器优先级规则

### P1：建议尽快清理

当前无额外 `P1` 文档清理项。

本轮已完成：

- `3-A` 主文档文件名与正文主题对齐。
- `3-A-2` 文档标题编号与主文档引用对齐。
- `Framework.md` 中已落地条目的旧“待补充”标记清理。
- `timeline system.md` 中的 `SpeedChangedEvent` 命名与调度协议文档统一。

### P2：下一执行阶段候选工作

- 当前未启动新执行阶段。
- 引擎层面的剩余工作图已整理到：
  - `stages/planning-gate/Engine Remaining Work Map and Phase 18 Candidates.md`
- 当前剩余主线按大类可分为：
  - 调度系统深化
  - 同步与恢复深化
  - 确定性与验证深化
  - 作者化与承载面
- 当前更建议优先考虑：
  - `Phase 18：Effect Metadata Schema Slice`
- 当前明确不建议在同一轮捆绑：
  - 新的 timeline 调度语义
  - 增量快照
  - rollback 契约重写
  - 第二个 demo slice
  - 大规模内容系统重构

---

## 6. 推荐工作顺序

后续工作建议按以下顺序推进：

1. 先按 `Global Phase Map and Current Position.md` 确认当前所处阶段。
2. 再参考 `stages/planning-gate/Post-MVP Scope Guardrails and Next-Step Plan.md` 与 `stages/planning-gate/Engine Remaining Work Map and Phase 18 Candidates.md` 选择单一窄主线。
3. 若继续按当前建议推进，优先先补 effect metadata schema 的最小自描述能力，再决定是否继续向更复杂的 hook/profile 组合深挖。
4. 只有在 metadata schema 的最小入口固定后，再考虑更复杂的内容配置面、调度语义或恢复契约深化。

**不建议的顺序：**

- 在 transport host 还没加固前就继续扩大量新 demo 技能。
- 在 Timeline driver 还没进入主线前就把复杂网络链式系统作为主目标。
- 在 recovery 刚完成最小 cross-driver 泛化后，立刻把新的 timeline 语义和新的恢复框架一起推进。
- 在验证平台雏形刚落地后，立刻把所有 effect / content / transport 维度都塞进 matrix。

---

## 7. 交接读取顺序

新对话或新协作者接手时，若 `.codex/handoffs/CURRENT.md` 已从 bootstrap placeholder 刷新为正式 mirror，则应优先读取它，并按其中 `authoritative_refs` 继续。

若当前尚无 active handoff，则建议按以下顺序阅读：

1. 本文件。
2. `Global Phase Map and Current Position.md`
3. `stages/README.md`
4. `tooling/Session Handoff Standard.md`
5. `tooling/Session Handoff Conditional Blocks.md`
6. `Checklist Maintenance Protocol.md`
7. `Engine Macro-Architecture.md`
8. `Framework.md`
9. `Window Service and Lifecycle Control Protocol.md`
10. `Scheduling Metric Change Protocol.md`
11. `Scheduling Adjustment and Window Grant Protocol.md`
12. `timeline system.md`
13. `attributes and buffs.md`
14. `Modifier Stacking and Attribute Evaluation Profiles.md`
15. `Listener Priority Resolution and Phase Profiles.md`
16. `base event function and communication system.md`
17. `State Snapshot and World Overwrite Protocol.md`
18. `Command and Event Core Structure and Serialization.md`
19. `detail in TOCTOU resolution.md`
20. `Event Bus Pipeline and Context Flattening Algorithm.md`
21. `stages/mvp/README.md`
22. `stages/host-separation-and-diagnostics/README.md`
23. `stages/multi-scheduler-expansion/README.md`
24. `stages/planning-gate/README.md`
25. 仅在需要追溯时，再读 `.codex/handoffs/history/` 或 `tmp.txt` 中与当前任务直接相关的片段。

---

## 8. 规划守门

进入任何新阶段规划前，建议先经过项目级阶段审查位：

- `stage-reviewer`

进入任何阶段收口前，建议再经过统一验证审查位：

- `verification-reviewer`

其职责是：

- 检查阶段命名是否准确
- 检查当前计划是否越界
- 检查是否遗漏已约定职责
- 检查是否把 backlog 内容误写成当前阶段必须项

协作入口见：

- `AGENTS.md`
- `.codex/agents/stage-reviewer.md`
- `.codex/agents/verification-reviewer.md`

---

## 9. 下次对话的建议起点

若下一次对话需要继续推进规划，优先做以下事情：

- 先经 `stage-reviewer` 审查新阶段命名、边界与职责覆盖。
- 先在 `stages/planning-gate/Engine Remaining Work Map and Phase 17 Candidates.md` 中选择单一窄主线。
- 再决定下一执行阶段是否优先做：
  - effect authoring surface
  - 更深的恢复诊断
  - 更清晰的内容承载边界

若下一次对话准备直接进入实现，建议先完成：

- 新执行阶段的正式命名。
- 新执行阶段的非目标清单。
- 对 `Core / Standard Components / Host / Driver` 的职责边界再确认一次。
- 准备对应阶段的手测入口与统一验证门。

---

## 10. 变更记录

### 2026-03-29

- 新建本文件，作为项目总清单、状态板与交接入口。
- 基于当前本地文档与 `tmp.txt` 历史对话，完成第一次全局状态归档。
- 明确项目当前阶段为“设计已收敛、实现未开工”。
- 提取并冻结了当前已确认的架构前提。
- 列出编码前优先补齐的关键缺口 `[3-C]`、`[2-A]`、`[2-B]` 与跨模块事件契约。
- 新增 `State Snapshot and World Overwrite Protocol.md`，正式补完 3-C。
- 将通信总览文档中的 3-B / 3-C 占位文字替换为 Obsidian 正式链接。
- 将 `[3-C]` 从 P0 缺口中移除，并调整推荐工作顺序。

### 2026-03-30

- 新增 `Window Service and Lifecycle Control Protocol.md`，正式固化 Lifecycle Control、Window Service、Focus 扩展与 `WINDOW_*` 协议事件。
- 明确 `TurnStartEvent / TurnEndEvent` 不属于 `Core`，而是 turn-like driver 在窗口生命周期之上投影出的兼容事件。
- 在 `timeline system.md` 与 `classical turn driver.md` 中补充对窗口协议文档的引用说明。
- 更新总纲 `Framework.md` 的进阶文档入口。
- 将 P0 中的“跨模块事件契约”缺口改写为剩余两部分：属性变化模板与调度器操作请求模板。
- 新增 `Scheduling Metric Change Protocol.md`，正式定义 `SchedulingMetricChangedEvent` 与 `SpeedChangedEvent` 的兼容关系。
- 新增 `Scheduling Adjustment and Window Grant Protocol.md`，正式定义 `ScheduleAdjustEvent`、`WindowGrantEvent` 与 `ActionAdvanceEvent` 的兼容关系。
- 在 `Window Service and Lifecycle Control Protocol.md` 中将 1-D-1 / 1-D-2 留空引用替换为正式 Obsidian 链接。
- 在 `timeline system.md` 与 `classical turn driver.md` 中补充对调度协议文档的引用说明，并明确 AV 数学只属于时间轴 driver 的内部解释。
- 将“跨模块事件契约”从 P0 缺口中移除，后续优先级回到 `[2-A]` 与 `[2-B]`。
- 新增 `Modifier Stacking and Attribute Evaluation Profiles.md`，正式补完 `[2-A]`，并明确默认公式只是官方 profile，不是唯一硬编码规则。
- 在 `attributes and buffs.md` 中将 `[2-A]` 占位替换为正式 Obsidian 链接。
- 在 `Framework.md` 中补充属性求值子文档入口。
- 新增 `Listener Priority Resolution and Phase Profiles.md`，正式补完 `[2-B]`，并明确事件优先级、监听器优先级与拦截器优先级三者分离。
- 在 `attributes and buffs.md` 中将 `[2-B]` 占位替换为正式 Obsidian 链接。
- 在 `Framework.md` 中补充监听器调度子文档入口。
- 将 `[2-A]` 与 `[2-B]` 均从 P0 缺口中移除，当前文档优先级已转入清理编号、命名与交叉引用。
- 将 `Event Validation Pipeline and TOCTOU Resolution.md` 重命名为 `Command and Event Core Structure and Serialization.md`，使 3-A 主文档文件名与正文主题对齐。
- 将 `Standard Validation Component and API Syntax Sugar.md` 的标题编号修正为 `3-A-2`。
- 清理 `Framework.md` 中已落地条目的旧“待补充”标记。
- 统一 `timeline system.md` 与调度协议文档中的 `SpeedChangedEvent` 命名。
- 新增 `M0 Core Skeleton Scope and Reserved Interfaces.md`，正式定义当前阶段不直接追求 MVP，而优先进入 M0 核心骨架实现。
- 在主清单中将项目阶段更新为“设计收口与实现规划阶段”，并将后续工作顺序切换为 `M0 -> M1/MVP`。
- 建立项目级 `AGENTS.md` 与目录化 `.codex/agents/` 配置，正式进入子 agent 协作模式。
- 启动 `M0` 首轮编码，创建 `core / standard_components / server / client / tests` 包结构。
- 实现 `BaseCommand / BaseEvent / World / EventBus / Lifecycle / Window Service` 的首批骨架。
- 实现最小 `classical turn` driver、`ServerHost / ClientHost` 与 `BasicAttack` 测试切片。
- 增加最小 JSON-like 序列化守门字段与 `schema_version` / `command_seq` / `origin_command_id` 预留位。
- 将项目版本约束固定为 Python `3.12`，并新增 `.python-version`。
- 引入 `WorldStateDTO` 作为纯数据世界导出边界，避免运行时 `World` 直接充当未来快照 DTO。
- 新增序列化守门与窗口绑定相关回归测试。
- 在测试切片中补上 custom command/event 的 registry/factory 重建链路。
- 安装 `python3.12`（`3.12.13`），并将项目 `.venv` 切换到 Python `3.12.13`。
- 通过 `.venv/bin/python -m pytest -q` 跑通当前 `M0` 回归：`11 passed`。
- 建立按业务分流的日志设施与根级 `config.json` 配置入口，并为测试会话引入历史日志压缩。
- 将 `project_setup.py` 收束为统一装配入口，补齐 `make_runtime / make_server_host / make_client_host` 以及 `make_basic_combat_*` 系列 helper。
- 新增 `tests/acceptance/test_m0_acceptance.py`，并将 `M0` 状态推进到“核心骨架可验收”。
- 新增 `M1 MVP Scope and First Vertical Slice.md`，正式定义 `M1` 的当前边界、首个 vertical slice 与验收条件。
- 在 `standard_components/drivers/classical_turn/projection.py` 中实现客户端 turn/window 投影，并补充相关集成测试。
- 新增 `demo/session.py` 与 `demo/cli.py`，形成本地 `ServerHost + ClientHost` 会话封装与终端 CLI 壳。
- 为 `demo` 新增独立日志分流，并通过 `tbge-demo` 提供本地可运行入口。
- 修正 `make_configured_client_host()` 未自动安装 demo slice client projection 的问题，并补充配置化 host 回归。
- 新增 `LocalBattleSession`、配置化 CLI 分支矩阵与默认 slice 装配相关回归。
- 将 `WINDOW_*` 生命周期调整为事件执行时生效，并将 `TURN_END` / 下一窗口开启的推进拆成两个阶段，以修正服务端与客户端的窗口观测时序。
- 修正 `WINDOW_RESUME` 无法恢复焦点命令窗口的问题，为后续 suspend/resume 保留正确闭环。
- 将 CLI 的非法目标与命令拒绝路径改为失败安全提示，并为未知目标分支补上回归。
- 将控制台 client 的 prompt、帮助文本、玩家阵营与启动/退出文案回收到根级 `config.json`。

### 2026-04-02

- 新增 `Global Phase Map and Current Position.md`，重新定义已完成工作的全局阶段划分与当前位置。
- 新增 `design docs/stages/README.md`，作为新的阶段目录入口。
- 将 `M6 / M7-A` 相关文档归档到 `design docs/stages/host-separation-and-diagnostics/`。
- 将 `M7-B / M7-C` 相关文档归档到 `design docs/stages/multi-scheduler-expansion/`。
- 将旧的阶段规划文档归档到 `design docs/stages/planning-gate/`。
- 保持已执行阶段文档正文不变，仅通过目录与索引重排阶段口径。
- 将项目当前阶段更新为“下一执行阶段规划门”，不再将 Timeline 接入表述为 MVP 尾项或当前执行阶段。
- 新增 `Phase 5 Sync Recovery and Re-attach Hardening.md` 与手测指引，正式记录 socket 手动重连恢复与 subprocess 快照注入一致性阶段。
- 新增 `tests/acceptance/test_phase5_acceptance.py`，固定 `Phase 5` 自动化验收边界。
- 将项目当前阶段更新为“`Phase 5` 已完成，重新回到规划门”。
- 新增 `client/console_app.py` 与 `tbge-client-console`，将控制台入口提升为 `client` 层正式入口。
- 新增 `tests/acceptance/test_m1_acceptance.py`，固定配置化 host、本地 session、控制台 client 与入口脚本的自动化验收边界。
- 新增 `M1 Manual Console Test Guide.md`，提供正式手动控制台验收步骤。
- 为客户端投影元数据、stale `TURN_END/WINDOW_END` 守卫，以及 CLI 的 `No active actor / No valid target / status` 分支补上回归。
- 用户已完成 `M1` 手动控制台验收，项目阶段切换到 `M2`。
- 新增 `standard_components/attributes/service.py` 与 `standard_components/effects/controller.py`，落下当前最小效果 / 修饰器 / 监听器切片。
- 为 demo slice 新增 `RALLY -> ATTACK_UP` 与 `POISON` 两条最小行为链，并在 CLI 中加入对应可见状态。
- 引入 `runtime.execution_role = authoritative / projection` 的最小执行画像区分，修正客户端回放权威事件时的重复派生问题。
- 在 `import_state()` 后重建效果监听器，补上当前切片最小的效果重建闭环。
- 新增 `RuntimeSnapshot`、`ServerHost.export_snapshot()`、`ClientHost.recover_from_snapshot()` 与 `LocalBattleSession.recover_client_from_server_snapshot()`，落下客户端快照恢复的最小实现。
- 新增 `tests/support/scenario_tools.py`，提供基于快照的通用场景注入工具，用于后续任意状态测试。
- 为客户端 projection 增加 stale `TURN_END` 防护，避免过期事件误触发效果衰减。
- 在 CLI 中加入 `poison` tick 明示输出，降低回合观感歧义。
- 新增 `M2 Acceptance and Scenario Injection Guide.md`，固定当前 `M2` 的通过标准与测试入口。
- 新增 `tests/acceptance/test_m2_acceptance.py` 与效果重建相关回归。
- 将项目阶段从“进入 `M2` 首切片”更新为“`M2` 首切片已基本收口”。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `75 passed`。
- 新增 `M3 Client Prediction and Snapshot Replay Slice.md`，固定当前 predictive client、pending buffer、快照恢复、静默重播与坏命令剔除的首切片边界。
- 为 `ClientHost` 引入 `PendingCommandRecord`、`predict_command()`、pending buffer 剪枝与重播路径。
- 为 `ClientHost` 引入 `SyncRecoveryReport` 与 `last_sync_recovery_report`，将快照恢复结果显式化为宿主可消费对象。
- 为 `LocalBattleSession` 引入 predictive local session builder、`reconcile_client_to_server_snapshot()` 与 `commit_next_predicted_command()`。
- 为 `GameRuntime` 与 `ClassicalTurnDriver` 补齐 `RuntimeSnapshot` 导入后的 projection state 同步与 prediction 元数据策略。
- 补齐 predictive client 在 `apply_event_payloads()` 后的 projection -> driver 状态回填，修正 `rally -> enemy auto turn -> next hero turn` 场景下的 stale window 拒绝。
- 将控制台 CLI 扩展为可配置 / 可命令行切换的 predictive 模式，并通过本地 `predict -> commit -> reconcile` 路径跑通最小交互闭环。
- 为控制台 CLI 新增 `sync / resync` 命令，使宿主层能直接查看最近一次恢复报告并主动触发权威快照刷新。
- 新增 `M3 Manual Predictive Console Test Guide.md`，固定当前 predictive CLI 的手测路径与通过判定。
- 新增 `tests/integration/test_client_prediction.py` 与 `tests/acceptance/test_m3_acceptance.py`，固定 `M3` 首切片当前通过标准。
- 修正 `predict_command()` 的入队时机，避免本地预测失败后脏命令仍残留在 `pending_command_buffer`。
- 在 `M3` 文档与验收中明确当前只支持单条 pending command，并新增对应回归测试。
- 为控制台 predictive 模式补上配置、入口参数与集成回归，固定 `run_configured_cli(..., predictive=...)` 与 `--predictive / --authoritative` 行为。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `92 passed`。
- 完成 `Phase 7 Timeline Advanced Scheduling Slice`，为 `timeline` 正式接入 `ScheduleAdjustEvent` 的首个解释。
- 在 `timeline` runtime 中新增 `SCHEDULE_ADJUST`、`ADVANCE + NORMALIZED_PERCENT` 与超量距离优先的 due actor 选择。
- 在 `basic_combat` 中新增 `PULL`，并将其打通到 CLI、projection、predictive、replay 与 subprocess smoke。
- 在 timeline `status` 中新增 `AV` 显示，并在 CLI 事件消息中显式输出 schedule adjust 结果。
- 新增 `Phase 7 Timeline Advanced Scheduling Slice.md`、对应手测文档、acceptance 测试，以及 `Engine Remaining Work Map and Phase 8 Candidates.md`。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `198 passed`。
- 完成 `Phase 8 Timeline Recovery Automation Slice`，为 `socket + predictive + timeline` 正式接入单次自动恢复。
- 在 session 与 CLI 中新增 `recover`、自动恢复状态对象、`transport` 诊断中的 `auto_recover / last_recovery`，并将命令提交与 `resync` 路径接入自动恢复。
- 新增 `Phase 8 Timeline Recovery Automation Slice.md`、对应手测文档、acceptance 测试，以及 `Engine Remaining Work Map and Phase 9 Candidates.md`。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `206 passed`。
- 完成 `Phase 9 Timeline Delay Slice`，为 `timeline` 正式接入 `ScheduleAdjustEvent(operation_kind=DELAY)` 的首个解释。
- 在 `timeline` runtime 中新增 `DELAY + NORMALIZED_PERCENT`，并补齐 `DELAY` 的 CLI、projection、predictive、replay 与 subprocess smoke。
- 新增 `Phase 9 Timeline Delay Slice.md`、对应手测文档、acceptance 测试，以及 `Engine Remaining Work Map and Phase 10 Candidates.md`。
- 为跨阶段验收流程补充“非对称注入验证”为标准步骤，并补齐覆盖 `Phase 6`、`Phase 7`、`Phase 8` 的 timeline 注入恢复测试。
- 完成 `Phase 10 Window Grant Minimal Slice`，为 `timeline` 正式接入 `WindowGrantEvent(AFTER_CURRENT, self)` 的首个解释。
- 在 `timeline` runtime 中新增 `WINDOW_GRANT`、self-grant 限定、stale `TURN_END` 防护，以及 granted window 的序列化 / 快照恢复覆盖。
- 新增 `Phase 10 Window Grant Minimal Slice.md`、对应手测文档、acceptance 测试，以及 `Engine Remaining Work Map and Phase 11 Candidates.md`。
- 为跨阶段验收流程补齐 `Phase 9` 与 `Phase 10` 的非对称注入恢复覆盖。
- 完成 `Phase 11 Timeline Foreign-Actor Window Grant Slice`，为 `timeline` 正式接入 `WindowGrantEvent(AFTER_CURRENT, foreign actor)` 的首个解释。
- 在 `timeline` runtime 中新增 foreign grant 的 hidden future slot 暂存、恢复与 speed-rescale，并补齐 stale `TURN_END` 的 foreign granted window 防护。
- 新增 `GRANT`、对应 CLI / 帮助 / 手测 / acceptance 测试，以及 `Engine Remaining Work Map and Phase 12 Candidates.md`。
- 为跨阶段验收流程补齐 `Phase 11` 的非对称注入恢复覆盖，显式验证 foreign granted hidden future slot 在 resync 后仍能恢复。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `257 passed`。
- 完成 `Phase 12 Timeline Immediate Insert Minimal Slice`，为 `timeline` 正式接入 `WindowGrantEvent(IMMEDIATE, foreign actor)` 的首个解释。
- 在 `timeline` runtime 中新增 immediate insert 的 suspend / resume、stale turn-end 防护、致死 suspended window 清理事件，以及 immediate 链路的序列化 / 快照恢复覆盖。
- 新增 `IMMEDIATE`、对应 CLI / 帮助 / 手测 / acceptance 测试，以及 `Engine Remaining Work Map and Phase 13 Candidates.md`。
- 汇总 post-MVP 结束至 `Phase 12` 的 timeline 执行文档到 `design docs/stages/timeline_T1/README.md`。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `276 passed`。
- 完成 `Phase 13 Cross-Driver Recovery Generalization Slice`，将 predictive socket recovery 从 timeline 特例推进到最小 cross-driver 泛化。
- 在 session / CLI / command help 中移除 timeline-only 的自动恢复资格表述，并为 `classical_turn` 补齐 predictive socket 的 `resync` 与命令提交自动恢复 smoke。
- 新增 cross-driver 的非对称 scheduler-state 注入恢复回归、对应手测文档、acceptance 测试，以及 `Engine Remaining Work Map and Phase 14 Candidates.md`。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `283 passed`。
- 完成 `Phase 14 Cross-Driver Determinism Matrix Slice`，将现有 driver / transport / recovery 组合沉淀为最小长期 determinism matrix。
- 新增 `tools/verification_platform/`、稳定状态摘要、canonical 场景矩阵、CLI 入口、对应手测文档、acceptance 测试，以及 `Engine Remaining Work Map and Phase 15 Candidates.md`。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `287 passed`。
- 完成 `Phase 15 Effect Authoring Surface Seed`，为现有效果机制补上最小 definition / registry / build 入口，并新增 CLI `effects` 作为开发者观察面。
- 新增 `standard_components/effects/models.py`、`standard_components/effects/authoring.py`、对应手测文档、acceptance 测试，以及 `Engine Remaining Work Map and Phase 16 Candidates.md`。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `294 passed`。
- 完成 `Phase 16 Effect Runtime Hook Profile Slice`，将 effect runtime hook 从 `effect_type` 分支推进为最小 profile 入口，并为 `POISON` 迁移到 profile 化路径。
- 新增 `Phase 16` 文档、作者化使用指南，以及 `Engine Remaining Work Map and Phase 17 Candidates.md`。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `296 passed`。
- 完成 `Phase 17 Authoring Documentation Standard Gate`，将作者化文档的长期放置规则、章节模板、完成定义与 discovery surface 同步边界固定为统一标准。
- 新增 `design docs/tooling/Authoring Documentation Standard.md`，并将两份 effect usage guide 归一化为标准样例。
- 新增 `tests/support/authoring_docs.py`、`tests/core/test_authoring_documentation_standard.py`、`tests/acceptance/test_phase17_acceptance.py`，为作者化文档标准补上最小自动检查。
- 新增 `Phase 17` 文档、手测指引，以及 `Engine Remaining Work Map and Phase 18 Candidates.md`。
- 当前自动化验证已推进到：`python3.12 -m pytest -q` -> `301 passed`。

### 2026-04-06

- 新增 `design docs/tooling/Session Handoff Standard.md` 与 `design docs/tooling/Session Handoff Conditional Blocks.md`，固定多会话 handoff 的长期协议、conditional block 注册表与 `Other` 审查规则。
- 新增 `.codex/handoffs/` 与 `.codex/handoff-system/` 的项目级目录骨架，分离 handoff 实例产物与项目专用 handoff skill 的开发资产。
- 新增 `.codex/handoff-system/docs/` 与 `templates/` 下的说明文档和 canonical handoff 模板，固定 `generate / accept / refresh current` 的项目内工作流。
- 更新 `design docs/tooling/README.md`、`AGENTS.md`、`.codex/README.md`、`.codex/agents/README.md` 与本文件，登记新的交接协议入口、读取顺序与安全停点交接要求。
- 将本文件中的 workspace 现实状态修正为“当前工作区现已是一个 git 仓库”，避免新 handoff 流程继续依赖过期事实。
