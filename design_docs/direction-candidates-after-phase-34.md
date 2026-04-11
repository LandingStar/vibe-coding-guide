# Direction Candidates — After Phase 34

## 背景

Phase 33–34 完成了入口面容错与结构化错误格式统一：

- `ErrorInfo` dataclass 统一了 Pipeline / MCP / CLI 的错误结构
- Pipeline 初始化容错（corrupt manifest 跳过 + `init_errors`/`init_warnings`）
- MCP 降级模式（`_require_pipeline()` → `ErrorInfo.to_dict()`）
- CLI `--debug` 模式（traceback + ErrorInfo JSON）
- 20 个 targeted tests 全部通过，69 个现有测试无回归

Phase 32 的收口清单 B1–B6 已满足，仅余 B7（用户确认升级）。

## 候选方向

### A. 用户确认升级 + v1.0 标记

- **做什么**：请用户审阅 `docs/first-stable-release-boundary.md` 中的 B7（显式确认升级），完成后为当前代码打 v1.0 标签、写 changelog。
- **依据**：`docs/first-stable-release-boundary.md` §3.1 B7；Phase 33–34 进一步增强了运行时健壮性，B1–B6+错误恢复均已到位。
- **前置**：B1–B6 已满足。
- **风险**：极低。

### B. CI/CD 集成

- **做什么**：pre-commit hook + GitHub Actions workflow，自动跑 `pytest` 和 `validate`。
- **依据**：`docs/project-adoption.md` 采用模型建议的校验层；`docs/first-stable-release-boundary.md` N8。
- **前置**：不依赖 v1.0。
- **风险**：需要 GitHub repo 配置。

### C. Validator 语义升级讨论

- **做什么**：设计 script-style validator 的长期协议——声明 `validate` 函数、发现入口、区分 check vs. full validator。
- **依据**：`docs/first-stable-release-boundary.md` N5；`review/research-compass.md` 中 Guardrails AI validator registry 借鉴点。
- **前置**：不依赖 v1.0。
- **风险**：纯设计讨论，需防止漂移。

### D. docs/ 权威文档精化

- **做什么**：更新 `docs/current-prototype-status.md` 反映 Phase 33–34 新增能力，补充 `docs/subagent-management.md` 中未覆盖的 delegation/escalation 运行时行为。
- **依据**：`docs/README.md` 中权威文档列表与实际代码能力存在 gap。
- **前置**：不依赖 v1.0。
- **风险**：低。

## 推荐分析

我倾向 **先走 A（v1.0 确认）**。理由：

1. Phase 32 收口清单的 B1–B6 已满足，Phase 33–34 进一步补齐了错误恢复和结构化错误格式——这正是 Phase 32 之后用户选择先做 B/D 而非 A 的原因。现在基础设施质量已大幅提升，是确认升级的最佳时机。
2. 方向 A 是极窄切片（用户确认 + 打标签 + changelog），完成后后续方向自然变成"稳定版之上的增量改进"。
3. B（CI/CD）和 C（validator）在 v1.0 之后做更合理——稳定版要保护的范围更明确。
4. D（docs 精化）可以与 A 同步或紧接着做。
