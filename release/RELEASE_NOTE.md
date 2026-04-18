# doc-based-coding-platform v0.9.3 (Preview)

协议/治理驱动工作流平台预览版本。

## 安装

下载 `doc-based-coding-v0.9.3.zip`，解压后按 `INSTALL_GUIDE.md` 说明安装即可。

```bash
pip install doc_based_coding_runtime-0.9.3-py3-none-any.whl
pip install doc_loop_vibe_coding-0.9.3-py3-none-any.whl
```

## 包含组件

| 组件 | 说明 |
|------|------|
| `doc-based-coding-runtime` | 平台运行时（Pipeline、CLI、MCP Server、PDP/PEP 治理引擎） |
| `doc-loop-vibe-coding` | 官方实例 pack（doc-loop 工作流的完整资产集） |

## CLI 入口

| 命令 | 说明 |
|------|------|
| `doc-based-coding info` | 查看已装载的 pack 信息 |
| `doc-based-coding validate` | 运行项目约束检查 |
| `doc-based-coding process` | 处理意图请求 |
| `doc-based-coding check` | 运行全量约束检查并输出诊断 |
| `doc-based-coding generate-instructions` | 生成 `copilot-instructions.md` |
| `doc-based-coding pack list\|install\|remove\|info` | Pack 管理 |
| `doc-loop-bootstrap` | 在目标项目中初始化 doc-loop 工作流骨架 |
| `doc-loop-validate-instance` | 校验官方实例 pack 完整性 |
| `doc-loop-validate-doc` | 校验文档合规性 |

## MCP 接入

```json
{
  "servers": {
    "doc-based-coding": {
      "type": "stdio",
      "command": "doc-based-coding-mcp"
    }
  }
}
```

支持 Copilot、Codex 及所有兼容 stdio 的 MCP 客户端。

## 已验证场景

- 双包构建（runtime 83KB + instance 48KB）
- 干净虚拟环境安装 + 所有 CLI 入口可用
- 空项目 bootstrap → 约束检查 → MCP 启动全链路通过

## 稳定面

Pipeline API、CLI、MCP Tools、Pack System、PDP 决策链、PEP 执行（dry-run）、Review 状态机、约束检查（C1–C8）、审计系统、Instructions Generator、Checkpoint、Validator Framework、Bootstrap/Validation 脚本。

完整变更历史见 [CHANGELOG.md](CHANGELOG.md)。
