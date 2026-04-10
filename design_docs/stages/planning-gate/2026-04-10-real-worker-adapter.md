# Planning Gate — Real Worker Adapter (LLM + HTTP)

- Status: **CLOSED**
- Phase: 15
- Date: 2026-04-10

## 问题陈述

平台的子 agent 管线（contract → worker → report → validate）仅有 StubWorkerBackend（返回合成 report），无法真正执行任何任务。`docs/subagent-management.md` 定义的 supervisor-worker 模式需要真实执行后端。

用户指出：一般工作以 Copilot/Codex 等工具自带子 agent 系统为主，仅在特化需求中使用外接 API。因此 LLM Worker 定位为"可选的外接执行后端"，而非平台默认执行路径。

## 切片计划

### Slice A — Worker 注册与抽象

**范围：**
- 创建 `src/workers/` 包
  - `__init__.py`
  - `base.py`：WorkerConfig dataclass (worker_type, api_key, base_url, model, timeout, max_retries)
  - `registry.py`：WorkerRegistry — 按 worker_type 注册和获取 worker 实例
- WorkerConfig 从环境变量或配置 dict 读取，API key 不硬编码
- 测试 registry 的注册/获取/未找到错误

### Slice B — LLM Worker (阿里云 DashScope / OpenAI-compatible)

**范围：**
- 创建 `src/workers/llm_worker.py`：
  - `LLMWorker(config: WorkerConfig)` 实现 WorkerBackend Protocol
  - `execute(contract) -> report`：
    1. 从 contract 提取 task + scope + required_refs → 构造 prompt
    2. 调用 OpenAI-compatible API (阿里云 DashScope 兼容 OpenAI SDK 格式)
    3. 解析 LLM 响应 → 构造 subagent report
    4. 错误处理：超时/API 错误/格式错误
  - 使用 stdlib `urllib.request`（不引入 openai SDK 依赖）
  - 重试策略：简单指数退避
- 单元测试：mock HTTP 调用，验证 contract→prompt 翻译和 response→report 转换
- 集成测试（需 API key，可 skip）：真实调用验证

### Slice C — HTTP Worker

**范围：**
- 创建 `src/workers/http_worker.py`：
  - `HTTPWorker(config: WorkerConfig)` — 向外部 API endpoint POST contract
  - 响应解析为 report
- 测试

**不做：**
- 不实现 subprocess worker（安全隔离需单独设计）
- 不引入第三方 LLM SDK（仅 stdlib）
- API key 不硬编码在代码中

## 验证门

1. `pytest tests/` 全部通过（无回归）
2. LLM Worker 单元测试覆盖 prompt 构建 + response 解析 + 错误处理
3. WorkerRegistry 可注册/获取/列出 worker
4. 至少一个真实 LLM 调用测试（可标记 skip 如无 key）
