# Direction Candidates — After Phase 32

## 背景

Phase 32 已交付 `docs/first-stable-release-boundary.md`，明确了：

- 15 类默认稳定入口 vs. 12 类实验/非阻塞入口
- 7 条 blocker（B1–B6 已满足，B7 待用户确认升级）
- 10 条 non-blocker（N1–N10）
- 默认 self-hosting 升级的 5 维判断标准

当前项目处于收口清单已定义但尚未执行首次正式 release 的阶段。

## 候选方向

### A. 用户确认升级 + v1.0 标记

- **做什么**：请用户审阅 `docs/first-stable-release-boundary.md` 中的 B7（显式确认升级），完成后为当前代码打 v1.0 标签、写 changelog。
- **依据**：`docs/first-stable-release-boundary.md` §3.1 B7；Phase 29 确立的两层边界收口条件已基本满足。
- **前置**：B1–B6 已满足；用户需确认收口清单无遗漏。
- **风险**：若用户认为尚需补充能力再升级，则此方向推迟。

### B. 错误恢复与重试策略

- **做什么**：为 Pipeline / CLI / MCP 入口补充结构化错误处理和可选重试。当前错误直接抛异常，用户看到的是 traceback。
- **依据**：`design_docs/phase-0-26-review.md` 中标记的运行时健壮性需求；`review/research-compass.md` 中 LangGraph durable state / interrupt 借鉴点。
- **前置**：不依赖 v1.0 标记，可独立推进。
- **风险**：scope 容易膨胀——需限定在入口面错误消息 + 重试骨架。

### C. CI/CD 集成

- **做什么**：pre-commit hook + GitHub Actions workflow，用于自动跑 `pytest` 和 `validate`。
- **依据**：`docs/project-adoption.md` 中采用模型建议的校验层；`docs/first-stable-release-boundary.md` N8 标记为 non-blocker 但属于自然后续。
- **前置**：不依赖 v1.0，但做完版本标记后价值更大。
- **风险**：需要 GitHub repo 配置；当前 repo 在 main 分支上直接开发。

### D. Validator 语义升级讨论

- **做什么**：设计 script-style validator 的长期协议——是否要求声明 `validate` 函数、如何发现可用入口、如何区分 check 和 full validator。
- **依据**：`docs/first-stable-release-boundary.md` N5；Phase 31 诊断已到位但语义本身未升级。`review/research-compass.md` 中 Guardrails AI validator registry 借鉴点。
- **前置**：不依赖 v1.0。
- **风险**：纯设计讨论，不产出代码，需防止讨论漂移。

## 推荐分析

我倾向 **先走 A 再视情况走 B 或 C**。理由：

1. Phase 32 的收口清单已覆盖 B1–B6 全部条件，仅余 B7（用户确认）。当前是距离 v1.0 最近的时刻。
2. 方向 A 是一个极窄的切片（用户确认 + 打标签 + changelog），完成后即可宣布首个稳定 release，后续切片（B/C/D）自然变成"稳定版之上的增量改进"，心理模型更清晰。
3. 方向 B（错误恢复）和 C（CI/CD）都不依赖 v1.0 但在 v1.0 之后做更合理——因为稳定版要保护的东西更明确。
4. 方向 D 是讨论性质，可在任何时间点插入，不紧急。

但如果用户认为在确认升级之前还有需要补的能力（比如错误恢复是必需的），那 B 应提前到 A 之前。
