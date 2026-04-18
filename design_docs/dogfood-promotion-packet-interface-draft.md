# Dogfood Issue Promotion + Feedback Packet — Interface Draft

## 文档定位

本文件是 `design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md` 的核心产物。

它把 `design_docs/dogfood-evidence-issue-feedback-boundary.md` 中已验证的 contract 字段集映射成可直接翻译为代码的数据结构和函数签名。本文件只做 docs-only interface draft，不包含实现代码。

---

## 1. 数据结构

### 1.1 EvidenceRef

对一条 evidence 的引用，不复制 evidence 正文。

```python
@dataclass
class EvidenceRef:
    path: str              # review/*.md 路径
    section: str | None    # 可选，指向文档内具体段落锚点
    summary: str           # ≤3 句话的 evidence 摘要
```

### 1.2 PromotionDecision

promotion threshold evaluator 的输出。每条 symptom 一个 decision。

```python
class PromotionVerdict(Enum):
    PROMOTE = "promote"
    SUPPRESS = "suppress"

@dataclass
class PromotionDecision:
    symptom_id: str                  # 唯一标识，格式 symptom-{seq}
    symptom_summary: str             # symptom 的 1 句话描述
    verdict: PromotionVerdict
    triggered_conditions: list[str]  # 命中的 T1-T4 条件 ID 列表
    suppressed_conditions: list[str] # 命中的 S1-S3 条件 ID 列表
    reason: str                      # 判断理由，≤3 句话
    evidence_refs: list[EvidenceRef] # 支撑该 symptom 的 evidence 引用
```

### 1.3 IssueCandidate

对应 boundary doc 中的 12 字段 issue candidate contract。

```python
class IssueCategory(Enum):
    TRANSPORT_CREDENTIAL_ENDPOINT = "transport/credential/endpoint"
    CONTRACT_DRIFT = "contract drift/schema drift"
    OUTPUT_GUARD_REJECTION = "output guard rejection"
    WRITEBACK_BOUNDARY = "writeback boundary"
    WORDING_ADOPTION_BOUNDARY = "wording/adoption boundary"
    WORKFLOW_STATE_SYNC_GAP = "workflow/state-sync gap"

class ImpactLayer(Enum):
    RUNTIME = "runtime"
    CONTRACT = "contract"
    WORKFLOW = "workflow"
    STATE_SYNC = "state-sync"
    WORDING = "wording"

class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class RootCauseHypothesis:
    description: str
    basis: str
    confidence: Confidence

@dataclass
class IssueCandidate:
    issue_id: str                              # 唯一标识，格式 IC-{seq}
    title: str                                 # surface: symptom [under condition]
    problem_statement: str                     # 3-6 句话
    category: IssueCategory
    impact_layers: list[ImpactLayer]           # ≥1
    minimal_reproducer: str                    # 独立段落
    expected: str                              # 描述 contract/behavior
    actual: str                                # 描述实际行为
    evidence_refs: list[EvidenceRef]           # ≥1
    evidence_excerpt: str                      # ≤10 行摘录
    environment: str                           # 按类型分层
    promotion_reason: str                      # 命中了哪条 T1-T4
    root_cause_hypothesis: RootCauseHypothesis | None  # 可选
    non_goals: list[str]                       # ≥1
```

### 1.4 FeedbackPacket

对应 boundary doc 中的 9 必选 + 3 可选字段 feedback packet contract。

```python
@dataclass
class FeedbackPacket:
    # 必选字段
    packet_id: str                    # 格式 fp-{date}-{seq}
    source_issues: list[str]          # issue_id 列表，≥1
    source_evidence: list[str]        # evidence 路径列表，≥1
    judgment: str                     # ≤3 句话
    next_step_implication: str        # 可操作的前进建议
    affected_docs: list[str]          # 需更新的文档面路径
    affected_layers: list[ImpactLayer]
    non_goals: list[str]
    confidence: Confidence

    # 可选字段
    supersedes: str | None = None     # 被替代的 packet_id
    blocking_issues: list[str] | None = None
    raw_data_pointers: list[str] | None = None
```

### 1.5 ConsumerPayload

按消费者边界矩阵裁剪后的 packet 子集视图。

```python
class ConsumerName(Enum):
    DIRECTION_CANDIDATES = "direction-candidates"
    CHECKLIST = "checklist"
    PHASE_MAP = "phase-map"
    CHECKPOINT = "checkpoint"
    HANDOFF = "handoff"
    PLANNING_GATE = "planning-gate"

@dataclass
class ConsumerPayload:
    consumer: ConsumerName
    fields: dict[str, Any]  # 只包含该消费者被允许消费的字段子集
```

---

## 2. 函数签名

### 2.1 evaluate_promotion

```python
def evaluate_promotion(
    evidences: list[EvidenceRef],
    existing_issues: list[IssueCandidate],
) -> list[PromotionDecision]:
    """
    对输入的 evidence 列表中的每个 symptom 做 promotion threshold 评估。

    行为：
    1. 从 evidences 中提取 symptom 列表（一条 evidence 可能包含多个 symptom）。
    2. 对每个 symptom，检查 T1-T4 触发条件和 S1-S3 抑制条件。
    3. 如果 symptom 已被 existing_issues 覆盖（S2），标记为 suppress。
    4. 返回每个 symptom 的 PromotionDecision。

    约束：
    - 不修改 evidences 或 existing_issues。
    - 不访问文件系统（evidence 内容通过 EvidenceRef.summary 传入）。
    """
    ...
```

### 2.2 build_issue_candidate

```python
def build_issue_candidate(
    decision: PromotionDecision,
    evidences: list[EvidenceRef],
    seq: int,
) -> IssueCandidate:
    """
    将一个 promote 判定转换为 IssueCandidate 结构。

    行为：
    1. 从 decision 中提取 symptom 信息。
    2. 从 evidences 中提取 evidence_refs 和 evidence_excerpt。
    3. 组装 12 字段的 IssueCandidate。

    前置条件：
    - decision.verdict == PROMOTE。

    约束：
    - title 必须符合 'surface: symptom [under condition]' 格式。
    - evidence_excerpt ≤10 行。
    - 不访问文件系统。
    """
    ...
```

### 2.3 assemble_feedback_packet

```python
def assemble_feedback_packet(
    candidates: list[IssueCandidate],
    evidences: list[EvidenceRef],
    seq: int,
    date: str,
    supersedes: str | None = None,
) -> FeedbackPacket:
    """
    将一批 issue candidates 和 evidence refs 组装成一个 FeedbackPacket。

    行为：
    1. 聚合 candidates 的 source_issues 和 evidences 的 source_evidence。
    2. 从 candidates 中推导 affected_layers、affected_docs。
    3. 生成 judgment 和 next_step_implication。
    4. 组装 9 必选 + 可选字段。

    约束：
    - candidates ≥1。
    - judgment ≤3 句话。
    - next_step_implication 必须是可操作的前进建议。
    - packet 一旦生成，不可修改（immutable）。
    """
    ...
```

### 2.4 dispatch_to_consumers

```python
def dispatch_to_consumers(
    packet: FeedbackPacket,
) -> dict[ConsumerName, ConsumerPayload]:
    """
    按消费者边界矩阵将 FeedbackPacket 裁剪为 per-consumer payload。

    行为：
    1. 对每个 ConsumerName，按边界矩阵提取允许的字段子集。
    2. 返回 dict[ConsumerName, ConsumerPayload]。

    消费者边界矩阵：
    - direction-candidates: judgment, next_step_implication, affected_layers, source_issues (ID only)
    - checklist: packet_id, judgment (≤1 句摘要), affected_docs
    - phase-map: packet_id, affected_layers (标签 only)
    - checkpoint: packet_id, judgment, next_step_implication, confidence
    - handoff: packet_id, judgment, next_step_implication, affected_docs, non_goals
    - planning-gate: 全部字段（通过 source_evidence 链接访问 evidence，不内联）

    约束：
    - 不修改 packet。
    - pointer-only 原则：状态面对 evidence 和 issue 只保留 pointer。
    - 单层消费原则：每个消费者只取指定字段。
    """
    ...
```

---

## 3. 数据流图

```
┌─────────────────────────────────────────────────────────┐
│                      输入                                │
│   evidences: list[EvidenceRef]                          │
│   existing_issues: list[IssueCandidate]                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │  evaluate_promotion()   │
         │  T1-T4 触发 / S1-S3 抑制 │
         └──────────┬──────────────┘
                    │
                    ▼
      list[PromotionDecision]
           │                │
     promote=True      promote=False
           │                │
           ▼                ▼
  ┌──────────────┐    (丢弃，留在
  │ build_issue_ │     review 文档)
  │ candidate()  │
  └──────┬───────┘
         │
         ▼
   list[IssueCandidate]
         │
         ▼
  ┌──────────────────────┐
  │ assemble_feedback_   │
  │ packet()             │
  └──────────┬───────────┘
             │
             ▼
       FeedbackPacket
             │
             ▼
  ┌──────────────────────┐
  │ dispatch_to_         │
  │ consumers()          │
  └──────────┬───────────┘
             │
     ┌───────┼───────┬──────────┬──────────┬──────────┐
     ▼       ▼       ▼          ▼          ▼          ▼
 direction checklist phase-map checkpoint handoff planning-gate
 candidates                                          (全部字段)
 (裁剪)   (裁剪)    (裁剪)    (裁剪)     (裁剪)
```

---

## 4. Contract → 数据结构映射表

| Contract 概念 | 数据结构 | 字段数 | 备注 |
|--------------|----------|--------|------|
| Evidence 引用 | `EvidenceRef` | 3 | path + section + summary |
| Promotion 判定 | `PromotionDecision` | 7 | T1-T4 / S1-S3 的结构化输出 |
| Issue Candidate (12 字段) | `IssueCandidate` | 14 | 12 contract 字段 + issue_id + impact_layers 拆为 list |
| Feedback Packet (9+3 字段) | `FeedbackPacket` | 12 | 9 必选 + 3 可选 |
| 消费者 Payload | `ConsumerPayload` | 2 | consumer name + 裁剪后字段 dict |

---

## 5. 开放问题（留给实现型 gate）

| # | 问题 | 当前决策 | 理由 |
|---|------|----------|------|
| O1 | IssueCandidate 和 FeedbackPacket 应持久化为文件还是内存对象？ | 留给实现型 gate | 当前 docs-only 场景下以文件为主，但组件化后可能需要结构化存储 |
| O2 | evaluate_promotion 中 symptom 提取是否需要 LLM 辅助？ | 留给实现型 gate | 当前人工可完成；组件化后视复杂度决定 |
| O3 | dispatch_to_consumers 是直接写文件还是返回 payload 由调用者写？ | 返回 payload | 保持函数纯度，写入由调用层控制 |
| O4 | packet_id 的 seq 计数器如何管理？ | 留给实现型 gate | dry-run 盲区 B2，当前 docs-only 场景人工管理可接受 |
