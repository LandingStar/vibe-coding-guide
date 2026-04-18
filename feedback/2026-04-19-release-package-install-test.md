# 2026-04-19 新发行包安装测试报告

## 测试目标

- 根据 workspace 中更新后的发行包重新执行安装测试。
- 验证新包重装后 runtime、pack 和 VSIX 的最小运行闭环是否仍然成立。
- 确认新 `.vsix` 引入的 `serverMode` / `diagnose` 面是否与 runtime 提供的入口点一致。

## 输入产物

- `doc-based-coding-0.1.0.vsix`，最后修改时间 `2026-04-19 00:25:19`
- `doc_loop_vibe_coding-0.9.3-py3-none-any.whl`，最后修改时间 `2026-04-19 00:25:08`
- `doc_based_coding_runtime-0.9.3-py3-none-any.whl`，最后修改时间 `2026-04-18 23:48:26`

## 测试环境

- OS: Windows
- Workspace: `test`
- Python 环境：workspace `.venv`，Python `3.12.8`

## 测试步骤

1. 读取 `.vsix` 与两份 wheel 的元数据、依赖和入口点。
2. 检查当前环境中已安装包版本，确认本轮属于同版本重装。
3. 使用 `pip install --force-reinstall --no-cache-dir` 强制重装本地 runtime wheel 与 pack wheel。
4. 运行 `doc-based-coding info`、`doc-based-coding validate`、`doc-based-coding process`。
5. 运行 `doc-loop-validate-doc --target .` 与 `doc-based-coding-mcp --help`。
6. 通过 `code --install-extension .\doc-based-coding-0.1.0.vsix --force` 测试本地 VSIX 覆盖安装，并检查扩展目录。

## 结果摘要

- 重装成功：runtime 与 pack wheel 均能强制重装。
- CLI 通过：`info`、`validate`、`process`、`doc-loop-validate-doc`、`doc-based-coding-mcp --help` 均成功。
- 治理状态通过：`doc-based-coding validate` 返回 `passed`，无 blocking constraints。
- VSIX 安装通过：`code --install-extension` 返回退出码 `0`，扩展目录中出现 `doc-based-coding.doc-based-coding-0.1.0`。
- 对齐关系通过：新 `.vsix` 暴露 `docBasedCoding.serverMode` 配置；runtime wheel 提供 `doc-based-coding-mcp` console script，可支撑 command 模式。

## 关键观察

- 这次更新不是版本号递增，而是同版本重打包：pack wheel 仍为 `0.9.3`，VSIX 仍为 `0.1.0`。
- 同版本重打包意味着默认安装路径可能静默跳过更新，本轮必须使用 `--force-reinstall` 和 `--force` 才能确认拿到新内容。
- 新 pack 安装后，`doc-loop-vibe-coding` 的 pack 描述已变为非空，说明确实装到了更新后的内容。

## 结论

- 就“是否能安装并维持最小运行闭环”而言，本轮测试通过。
- 下一步更应该先处理发布资产一致性问题，而不是直接进入更广的 UI 手测。