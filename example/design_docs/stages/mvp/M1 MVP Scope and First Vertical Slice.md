# 📄 实现规划文档：M1 / MVP 范围与首个垂直切片

**(Implementation Plan: M1 MVP Scope & First Vertical Slice)**

## 1. 文档定位

本文件用于定义项目在 `M0` 之后进入的**第一条最小可行闭环**。

它不再关注“核心骨架是否成立”，而是关注：

- 如何在不破坏 `M0` 边界的前提下跑通一条真实可操作的战斗链路
- 当前 `M1` 只包含哪些范围
- 首个垂直切片已经实现到什么程度
- 哪些内容仍明确留在 `M2+`

本文件与以下文档配套使用：

- [[Project Master Checklist|项目总清单与状态板]]
- [[M0 Core Skeleton Scope and Reserved Interfaces|M0 核心骨架范围与预留接口]]
- [[classical turn driver|经典回合制组件]]
- [[Window Service and Lifecycle Control Protocol|窗口服务核心库与生命周期控制协议]]

---

## 2. 当前阶段判断

`M0` 已经完成骨架验证并具备验收条件，因此当前阶段正式切换为：

- **`M1 / MVP`**

这里的 `M1` 并不追求“完整玩法系统”，而是追求：

- 让服务端与客户端装配的同一套 `Core` 真正跑通一条本地闭环
- 让窗口协议、驱动推进、命令序列化、客户端投影与最小表现壳协同工作
- 通过最小 vertical slice 检查当前抽象是否真的好用

---

## 3. `M1` 当前范围 (In Scope)

当前 `M1` 明确包含以下内容：

- `1v1` 固定战斗样例
- `classical turn` 作为唯一启用的 driver
- `basic_combat` 作为唯一 demo slice
- 本地进程内的 `ServerHost + ClientHost`
- 客户端事件投影
- 本地 `LocalBattleSession`
- 控制台 client / 终端 CLI 作为第一层表现壳
- 根配置驱动的默认 slice bootstrap
- 根配置驱动的控制台 client 文案与交互参数

当前 `M1` 的目标不是扩大量，而是验证：

1. `Server` 侧权威推进能稳定产出事件流。
2. `Client` 侧能够仅通过事件流重建当前窗口与最小 turn 投影。
3. 上层调用者可以不碰底层 runtime 细节，只通过 session/CLI 使用这套引擎。

---

## 4. 首个垂直切片：`basic_combat`

当前已经落地的首个垂直切片包含：

- `demo/basic_combat.py`
  - 提供 `BasicAttackCommand`
  - 提供 `DamageEvent`
  - 提供 demo world builder
  - 提供最小 command / event validator 与 executor

- `standard_components/drivers/classical_turn/projection.py`
  - 客户端侧消费 `ROUND_* / TURN_* / WINDOW_*`
  - 维护最小 turn 投影状态
  - 在客户端重建当前窗口焦点

- `demo/session.py`
  - 提供 `LocalBattleSession`
  - 屏蔽本地 server/client 命令往返细节
  - 提供 `start()`、`submit_basic_attack()`、`current_actor_id()` 等最小会话接口

- `demo/cli.py`
  - 提供可运行的本地 battle CLI
  - 支持 `help / status / attack / quit / exit`
  - 将敌方回合作为自动行动处理
  - 提供 `tbge-demo` 入口

- `client/console_app.py`
  - 提供 `client` 层正式控制台入口
  - 暴露 `tbge-client-console`
  - 用于 `M1` 手动控制台验收

- `project_setup.py`
  - 提供 `make_basic_combat_*` 与 `make_configured_*` 装配入口
  - 通过 `config.json` 的 `bootstrap.default_slice` 选择默认 demo slice

---

## 5. 当前明确不做的内容 (Out of Scope)

以下内容仍不属于当前 `M1` 的交付目标：

- Buff / Modifier / Listener 标准库的完整实现
- 时间轴 driver
- 客户端预测
- 权威快照覆盖与静默重播
- 高级连锁/LIFO
- 图形界面、动画、音效
- 多种 demo slice 并行接入
- 真实网络层

这些内容保留到 `M2+` 继续推进。

---

## 6. 当前实现的价值

这个首个垂直切片主要验证了三件事：

1. `M0` 的抽象不是空架子。
   - `Window Service`
   - `classical turn driver`
   - `Command / Event`
   - `Server / Client`
   现在已经能组成一条真实可执行链路。

2. 客户端投影并不需要偷用服务端对象。
   - 当前客户端只通过序列化事件恢复 turn 状态与当前窗口焦点。

3. 外围使用者可以站在更高一层工作。
   - `LocalBattleSession`
   - `CLI / Console Client`
   说明未来的 UI / 网络壳可以继续建立在更稳定的装配层之上。

4. 当前控制台表现壳已经不再是纯测试脚本。
   - 当前存在正式可启动入口
   - CLI 文案、prompt 与玩家阵营语义已回收到 `config.json`

---

## 7. 当前 `M1` 的验收标准

当前阶段可以视为“首个垂直切片成立”，当且仅当以下条件持续成立：

1. `make_configured_server_host()` 与 `make_configured_client_host()` 能在默认 slice 下跑通 battle start。
2. 客户端在收到服务端启动事件后，能够重建当前焦点窗口与当前 actor。
3. `LocalBattleSession` 能在不直接操作底层 runtime 的前提下跑通一回合。
4. 控制台 client 至少覆盖：
   - `help`
   - `status`
   - `attack`
   - `quit / exit`
   - 未知命令
   - 非法目标的失败安全提示
5. 当前自动化回归持续通过。
6. 控制台入口可由 `tbge-client-console` 或 `python3.12 -m client.console_app` 启动。

## 7.1 当前明确边界

当前 `M1` 到此为止，边界明确如下：

- **已包含**
  - 最小本地双端闭环
  - 一种 driver
  - 一种 demo slice
  - 一种控制台 client 壳
  - 最小 battle 状态显示与命令输入

- **仍不包含**
  - 第二种行为或技能体系
  - Timeline driver
  - Buff / Modifier / Listener 标准库
  - 客户端预测
  - 快照恢复
  - 真实网络层

这意味着 `M1` 的结果是：

- 一个**最基础但可运行、可手动控制、可通过控制台验收**的 client/server 本地样例。

## 7.2 手动验收入口

手动控制台测试步骤见：

- [[M1 Manual Console Test Guide|M1 手动控制台测试指引]]

---

## 8. 当前验收状态

截至当前版本：

- 自动化验收：已通过
- 手动控制台验收：已通过

当前阶段更准确的状态应视为：

- **`M1` 已完成自动化与手动控制台验收，可作为进入 `M2` 的稳定基线**

---

## 9. `M1` 的下一步建议

当前最合理的继续方向是：

1. 以当前 `basic_combat` vertical slice 作为基线进入 `M2`。
2. 在不破坏 `M1` 验收边界的前提下扩效果、修饰器和监听器切片。
3. 继续保持 demo 装配和 `Core` 边界分离。

当前不建议的方向：

- 为还不存在的第二个 slice 提前写大而全注册框架
- 在 `M1` 阶段直接跳去实现 Timeline、快照重播或复杂 Buff 系统
