# Continue Research

## 产品定位

Continue 是一个面向开发工作流的开源 AI 平台，强调：

- repo 内规则
- PR checks
- 事件触发 agents
- IDE / CLI / 云端联动

它不是完整的“治理驱动平台”，但在“规则文件即行为约束”这一层非常接近我们关心的问题。

## 关键机制

- Rules 使用 markdown 文件承载，并用于组装 system message。
- 规则加载有明确优先级：Hub assistant rules、referenced Hub rules、本地 workspace rules、global rules。
- Checks 也是 markdown 文件，包含 YAML frontmatter 和 prompt body。
- Checks 固定在 PR open 时运行；Agents 则可以由 schedule、issue、CI failure、webhook 等事件触发。
- `.agents/` 被 Continue 明确视作跨工具的 AI agent 配置目录标准之一。

## 对我们最有价值的点

- 把规则写成 repo 内文件，而不是埋进代码或远端配置。
- 明确本地、全局、云端三层来源及覆盖顺序。
- 区分 `checks` 和 `agents`：
  - `checks` 是固定触发、以 pass/fail 为目的
  - `agents` 是事件驱动、以自动化任务为目的
- 强调“一条 check 只管一个问题”，避免 prompt 过宽。

## 与我们目标的差异

- Continue 的核心更偏开发自动化与 PR review，不是平台级治理模型。
- 它对 human review 有支持，但不是我们这种“人通过 AI 间接治理文档”的中心模型。
- 子 agent 管理不是它的重点，更多是单 agent + event automation。

## 对子 agent 管理的启发

直接启发有限，但它给了两个很好的边界：

- 不要把所有治理都塞进一个大 agent prompt。
- 规则与自动化任务最好拆成独立、可发现、可覆盖的文件单元。

## 我们可吸收的设计点

- 项目内 `rules/` 或等价 pack 文件结构
- 明确的优先级链
- checks 与 general agents 分层
- markdown + frontmatter 作为轻量扩展载体

## 当前不应直接照搬的点

- 不应把平台收缩成 PR/issue 驱动系统
- 不应把“agent 文件”直接等同于完整 pack 抽象

## 主要来源

- https://docs.continue.dev/customize/deep-dives/rules
- https://docs.continue.dev/checks/reference
- https://docs.continue.dev/checks/best-practices
- https://docs.continue.dev/mission-control/beyond-checks
- https://github.com/continuedev/continue
