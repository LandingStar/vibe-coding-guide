# RuntimeBridge 注入 — Direction Analysis

## 问题陈述

CLI (`src/__main__.py`)、MCP (`src/mcp/server.py`)、VS Code Extension 三入口各自独立完成：
1. 项目根目录定位
2. `Pipeline.from_project(root)` 初始化
3. Worker 配置（LLM API key、model 选择）
4. User config 加载

重复逻辑 → 行为不一致风险 + 新入口需要重新发明同样步骤。

## 现有基础设施

| 组件 | 位置 | 作用 |
|------|------|------|
| `WorkerBackend` Protocol | `src/interfaces.py` | LLM 调用抽象 |
| `LLMWorker` | `src/workers/llm_worker.py` | OpenAI-compatible 实现 |
| `Pipeline.from_project()` | `src/workflow/pipeline.py` | Pack 加载 + Pipeline 构造 |
| `UserConfig` | `src/pack/user_config.py` | 全局用户偏好 |
| `AdapterRegistry` | `src/adapters/registry.py` | Worker 注册 |

## 设计方向

### 方案 A: 最小 RuntimeBridge Facade

新增 `src/runtime/bridge.py`：

```python
class RuntimeBridge:
    """统一初始化入口，封装 Pipeline + Worker + Config 生命周期。"""
    
    def __init__(self, project_root: Path, *, dry_run: bool = False):
        self._config = UserConfig.load()
        self._worker = self._create_worker()
        self._pipeline = Pipeline.from_project(project_root, dry_run=dry_run)
    
    @property
    def pipeline(self) -> Pipeline: ...
    @property
    def worker(self) -> WorkerBackend: ...
    @property
    def config(self) -> UserConfig: ...
    
    def _create_worker(self) -> WorkerBackend:
        # 根据 config 选择 worker 实现
        ...
```

各入口只需：`bridge = RuntimeBridge(root)` → `bridge.pipeline` / `bridge.worker`。

**优点**：改动小，不破坏现有接口，向后兼容。
**缺点**：仅是浅层 facade，不解决生命周期管理（如 worker 连接池、graceful shutdown）。

### 方案 B: 带生命周期的 RuntimeContext

在方案 A 基础上加 context manager：

```python
class RuntimeBridge:
    async def __aenter__(self): ...
    async def __aexit__(self, *exc): ...
```

**优点**：为未来 async worker、连接池、multi-agent 协调预留接口。
**缺点**：引入 async 会影响当前同步入口（CLI/MCP 当前均为同步）。

### 方案 C: 延迟实施

当前三入口的初始化代码量极小（< 10 行），不构成实质痛点。等 multi-agent 运行时真正需要共享状态时再提取。

**优点**：零改动。
**缺点**：不阻塞但也不推进架构清洁度。

## 推荐

**方案 A**（最小 facade）— 现在实施。理由：
1. 改动可控（新增 1 文件 + 修改 3 入口各 ~5 行）
2. 不引入 async 复杂度
3. 为后续 multi-agent 提供明确扩展点
4. 与 Multica insights 建议一致

## 实施切片

1. 新增 `src/runtime/__init__.py` + `src/runtime/bridge.py`
2. `RuntimeBridge.__init__` 统一 config + worker + pipeline 初始化
3. CLI 入口改用 `RuntimeBridge`
4. MCP GovernanceTools 改用 `RuntimeBridge`
5. 测试：初始化正确性 + dry_run 传递 + config 覆盖
6. Write-back
