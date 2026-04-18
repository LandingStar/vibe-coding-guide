# 问题反馈 005: `0.1.1` 发行包未表现出远程 Git 操作拦截能力

## 严重性

- High

## 问题类型

- 功能验证失败 / 发布产物一致性

## 现象

- 用户说明已新增“拦截远程 git 操作”功能，并要求基于 workspace 中的新包进行测试。
- `doc-based-coding-0.1.1.vsix` 可以成功安装，但与 `0.1.0` 对比后，`extension/dist/extension.js` 在排除版本字符串后没有非版本逻辑差异。
- `governance_decide` 对 `terminal-command: git push origin main`、`git fetch origin`、`git clone ...` 均返回 `ALLOW`。
- 真实黑盒命令中，本地 bare remote 的 `git push -u origin main` 已成功推送，`git fetch origin` 未被阻断，`git clone <local remote>` 也实际执行到克隆阶段。
- decision log 中记录的相关终端命令结果同样均为 `ALLOW`。

## 复现步骤

1. 使用 `code --install-extension .\doc-based-coding-0.1.1.vsix --force` 安装当前 `0.1.1` VSIX。
2. 调用 `governance_decide`，输入 `terminal-command: git push origin main`、`terminal-command: git fetch origin`、`terminal-command: git clone ...`。
3. 观察这些输入均返回 `ALLOW`，没有命中远程 git 拦截。
4. 在本地测试仓库上执行 `git push -u origin main`、`git fetch origin`、`git clone <local remote>`。
5. 观察远程命令可实际执行，decision log 也未出现 `BLOCK`。

## 预期结果

- 如果该特性已进入当前发行包，远程 git 命令应当能被明确识别，并表现出与“拦截”声明一致的治理结果或用户可见反馈。

## 实际结果

- 当前 `0.1.1` 发行包中的远程 git 命令仍走通用终端治理路径，未观察到任何专门的拦截判定或阻断行为。

## 影响

- 当前发行包无法支撑这项新功能的有效验证。
- 测试者可能以为自己已拿到包含新功能的包，实际测试到的仍是旧行为。
- 若功能实现与打包内容持续偏离，后续 release 测试会不断重复低价值的黑盒验证。

## 建议修复

- 也许可以在发布前加入一条“非版本差异 + 关键特性 smoke test”检查，确认新逻辑确实进入 VSIX。
- 可以把远程 git 命令模式或命中结果暴露到 `diagnose` / decision log 中，降低黑盒定位成本。
- 如果该特性其实尚未进入 release，也许可以先在版本说明或测试入口说明里明确这一点，避免继续围绕错误产物做验证。