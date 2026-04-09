# Post-MVP Scope Guardrails and Next-Step Plan

## 1. 文档定位

本文件用于回答两个问题：

1. `post-MVP` 阶段到底应该包含什么。
2. `post-MVP` 阶段明确不应该做什么。

它的目标不是继续发散路线，而是**防止 post-MVP 失控膨胀**。

后续若出现“这个需求听起来也很有用”的情况，应先回到本文件判断它是否真的属于当前阶段。

---

## 2. Post-MVP 应包含的内容

`post-MVP` 仍然应围绕“引擎底层能力增强”展开，而不是转向内容堆叠或产品外围。

当前建议只包含以下四类工作：

### 2.1 传输层加固

- socket transport 的错误语义
- connect / attach / shutdown 的稳定契约
- 超时、断链、失败上抬到 host / CLI 的方式
- 为未来 websocket 或远程 adapter 预留更清晰的边界

### 2.2 同步与调试工具增强

- 更明确的 sync / recovery 状态输出
- 更系统的 desync 场景注入
- 更清晰的宿主侧状态检查接口
- 更稳定的手动调试 CLI 能力

### 2.3 Timeline driver 主线接入

- 先进入 authoritative 主线
- 再进入 predictive / replay / resync
- 固定 Timeline 下的 token / binding / window 语义

### 2.4 确定性与回归测试增强

- transport 回归
- 双端一致性回归
- 快照与恢复回归
- Timeline 接入后的时序回归

---

## 3. 实现边界

为防止 post-MVP 范围过宽，当前阶段必须遵守以下边界：

### 3.1 一次只推进一条窄主线

- 不同时推进 transport 韧性、Timeline 全接入、复杂内容扩展。
- 每一轮只允许有一个“主切片”。

### 3.2 仍以 `basic_combat` 为基准切片

- post-MVP 的底层增强，默认仍在 `basic_combat` 上验证。
- 只有当底层接口稳定后，才允许新增第二个 demo slice。

### 3.3 不主动改写 `Core` 契约

- `Core` 当前边界已经够稳定。
- 除非出现真实阻塞，否则 post-MVP 不应把工作演变为“重写核心架构”。

### 3.4 Timeline 延后到 transport 更稳之后

- Timeline 是重要方向，但当前不应抢先于 transport 韧性。
- transport 的错误语义、状态输出、调试入口未稳定前，不建议把 Timeline 拉入主线。

### 3.5 所有新增 CLI 指令必须满足三件事

- 有 `help` 详细说明
- 有文档记录
- 有自动化回归

---

## 4. 明确禁止的内容

以下内容当前明确禁止进入 post-MVP 主线：

### 4.1 禁止继续堆 demo 内容

- 不继续大量新增技能
- 不继续新增复杂效果链
- 不把 demo 扩成内容项目

### 4.2 禁止提前做产品外围

- 房间系统
- 匹配系统
- 账号系统
- 存档/数据库
- UI 图形化大改
- 联网大厅

### 4.3 禁止把 transport 做成大而全网络框架

- 不直接跳到 websocket + 房间 + 多客户端并发
- 不直接做远程部署、NAT、认证、网关
- 不做“先造通用网络平台，再回头接游戏”

### 4.4 禁止把 Timeline 和网络重构捆绑在同一轮

- Timeline 接入必须在单独受控的切片里推进
- 不能一边改 transport，一边改 driver 主线，一边改快照契约

### 4.5 禁止为了“未来也许会用”先造过量抽象

- 不提前写 plugin 平台
- 不提前写过度泛化的 transport registry
- 不为了多游戏品类把当前切片抽成过厚框架

---

## 5. 当前建议的下一步功能

当前建议把下一步功能明确收成：

## `M7-A：Transport Resilience and Sync Diagnostics`

它的目标是：

- 让当前 socket transport 更稳
- 让 transport/sync 问题更容易观察
- 不在本轮正式进入 Timeline 主线

### 5.1 本轮应包含

- 明确 transport 状态报告对象
- 明确 transport 错误分类与输出
- 给 CLI 增加 transport 诊断指令
- 给 CLI 增加最小连接检查能力
- 增加 attach / disconnect / timeout 类测试骨架

### 5.2 本轮建议优先实现的 CLI 能力

- `transport`
  - 查看当前 transport 模式、连接目标、基础状态
- `ping`
  - 主动探测当前 server 是否可达
- 更清晰的 `sync` 输出
  - 区分 transport 问题与逻辑恢复问题

### 5.3 本轮明确不做

- Timeline authoritative 接入
- reconnect 自动化策略
- websocket transport
- 多客户端房间

---

## 6. 阶段顺序建议

当前 post-MVP 的推荐顺序如下：

1. `M7-A`
   - transport 韧性与同步诊断
2. `M7-B`
   - Timeline authoritative 首切片
3. `M7-C`
   - Timeline predictive / replay / resync
4. 更后续阶段
   - 增量快照
   - 更复杂恢复策略
   - 更远程化的 transport adapter

---

## 7. 当前结论

`post-MVP` 不是“随便加功能”的阶段，而是：

- 继续加固底层
- 控制范围
- 保持每一步都能验收

如果后续某项工作不属于：

- transport 韧性
- 同步调试
- Timeline 主线接入
- 确定性/回归增强

那它大概率就不应该进入当前的 post-MVP 主线。
