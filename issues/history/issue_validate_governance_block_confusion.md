# Issue: `doc-based-coding validate` 容易把“治理阻塞”误判成“命令运行失败”

## 标题

`doc-based-coding validate` 在命令成功执行但命中治理约束时，输出语义不够清晰，容易让用户和上层 agent 误判为“指令运行失败”

## 背景

在一个已经正确安装 `doc-based-coding` / `doc-loop` 且 bootstrap 正常的 workspace 中，执行以下命令：

```powershell
.\.venv-doc-based-coding\Scripts\doc-based-coding.exe info
.\.venv-doc-based-coding\Scripts\doc-based-coding.exe validate
.\.venv-doc-based-coding\Scripts\doc-loop-validate-doc.exe --target .
```

其中：

- `info` 能正确识别本地 pack
- `doc-loop-validate-doc` 能通过
- 但 `validate` 因缺少 planning-gate 文档触发 `C5`

这属于“平台运行正常，但项目当前被治理规则阻塞”的情况，而不是安装损坏、命令不可用或运行时异常。

## 复现步骤

1. 安装 preview release 的 runtime 与 `doc-loop` instance pack
2. 对项目执行 bootstrap，使其具备 `.codex/`、`design_docs/`、`AGENTS.md`
3. 保持项目尚未创建 planning-gate 文档
4. 执行：

```powershell
.\.venv-doc-based-coding\Scripts\doc-based-coding.exe validate
```

## 当前表现

命令输出类似：

```json
{
  "violations": [
    {
      "constraint": "C5",
      "message": "No planning-gate document found. Create one before large-scale implementation.",
      "severity": "block"
    }
  ],
  "has_blocking": true
}
```

随后终端还会出现：

```text
⚠ Blocking violations found.
```

在很多终端、IDE agent、自动化包装层里，这类表现会被自然理解为：

- 命令失败了
- 安装有问题
- 服务状态异常
- 指令没有正确运行

但实际上：

- runtime 正在正常工作
- pack 已正常加载
- 文档脚手架也可能已经通过校验
- 真正的问题只是“当前阶段不允许继续进入实现”

## 期望表现

应显式区分两类状态：

1. **命令执行状态**
   - 命令是否正常运行完成
   - runtime / pack / parser 是否工作正常

2. **治理决策状态**
   - 当前项目是否被某条约束阻塞
   - 若被阻塞，阻塞原因是什么

也就是说，应让用户一眼看出：

> “命令运行成功，但项目当前被治理规则阻塞”

而不是让用户自己从上下文里推断这不是安装失败。

## 影响

这个问题会带来几类实际负面影响：

- 用户误以为安装失败，重复排查环境
- agent 误以为命令出错，转而去检查 PATH、MCP、venv，而不是去补 planning-gate
- 上层自动化如果只看退出码或警告文本，可能把“治理阻塞”错误归类为“系统异常”
- 使首次接触 `doc-loop` 的用户难以理解平台是在“执行治理”，而不是“报错”

## 建议改进

### 方案 A：明确状态字段

在输出中增加类似字段：

```json
{
  "command_status": "ok",
  "governance_status": "blocked",
  "blocking_constraints": ["C5"]
}
```

这样 agent 和用户都能明确区分“运行成功”和“治理阻塞”。

### 方案 B：改进终端提示文案

将当前：

```text
⚠ Blocking violations found.
```

改为更明确的表述，例如：

```text
Validation completed successfully, but the workspace is currently blocked by governance constraints.
Blocking constraint(s): C5
Suggested next step: create a planning-gate document.
```

### 方案 C：区分退出码语义

如果仍希望在“治理阻塞”时返回非零退出码，也建议在文档中明确说明：

- 非零退出码不一定表示命令运行异常
- 某些退出码表示 runtime error
- 某些退出码表示 governance block

最好为这两类情况分配不同退出码。

### 方案 D：给首次用户更直接的引导

在命中 `C5` 时直接附带上下文提示，例如：

```text
The platform is installed and running correctly.
This workspace is blocked because no planning-gate document exists yet.
Create a planning-gate document before implementation.
```

## 为什么这个问题重要

`doc-based-coding` / `doc-loop` 的核心价值之一是把“治理约束”前置为开发流程的一部分。  
如果用户把治理阻塞误读成运行失败，那么平台最重要的能力就会在交互层被弱化，甚至被误解为“工具不稳定”。

因此，这不是一个纯文案问题，而是一个会影响 adoption 和 agent 集成质量的交互语义问题。

## 附：本次实际观察到的判断链

本次排查中：

- `doc-based-coding info` 正常
- `doc-loop-validate-doc` 正常
- `doc-loop-validate-instance` 正常
- `doc-based-coding-mcp` 可启动
- 只有 `validate` 命中 `C5`

因此可以确认：

> 当前现象本质上是“治理阻塞被误感知为运行失败”，而不是平台安装或服务状态异常。
