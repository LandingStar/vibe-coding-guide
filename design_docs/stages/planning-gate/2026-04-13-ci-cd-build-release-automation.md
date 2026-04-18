# Planning Gate — CI/CD Build & Release Automation

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-13-ci-cd-build-release-automation |
| Scope | 双包 wheel 构建、测试、版本校验、release 打包的本地自动化脚本 |
| Status | **COMPLETED** |
| 来源 | `release/README.md` §发布流程 / CI 配置（待办）、dogfood 反馈 |
| 前置 | 双包标准已固定、版本一致性检查脚本已存在 |
| 测试基线 | 823 passed, 2 skipped |

## 问题陈述

当前双包 wheel 构建、测试执行、版本校验、release zip 打包全部依赖手动操作。这导致：

1. 版本 bump 时容易遗漏某个 pyproject.toml 或 pack-manifest.json
2. 构建产物完整性（wheel 内容物、入口点）没有自动验证
3. release zip 打包步骤容易遗漏文件或包含旧产物
4. `build/` 目录下的旧副本不会被自动清理

## 目标

创建一套本地自动化脚本，覆盖完整的 build-test-package 流程。**不做** GitHub Actions 或远程 CI 配置（当前项目无公开仓库需求）。

**做**：
- `scripts/build.py`：一键构建双包 wheel（含 clean build、版本校验、内容物验证）
- `scripts/release.py`：一键打包 release zip（含双 wheel + INSTALL_GUIDE.md + RELEASE_NOTE.md + README.md）
- 在 `build.py` 中集成 `release/verify_version_consistency.py` 的校验逻辑
- 在 `build.py` 中验证 wheel 内容物完整性（检查 .py 文件数量和关键入口点）

**不做**：
- GitHub Actions / 远程 CI 配置
- PyPI 发布支持
- 跨平台构建矩阵
- 自动 git tag / commit

## 交付物

### 1. `scripts/build.py`

功能：
1. 清理旧 build 产物（`build/`、`dist/`、`*.egg-info/`）
2. 运行版本一致性检查
3. 构建 runtime wheel（`python -m build .`）
4. 构建实例包 wheel（`python -m build ./doc-loop-vibe-coding`）
5. 验证 wheel 内容物（.py 文件数量 ≥ 预期阈值、关键入口点存在）
6. 输出构建摘要

### 2. `scripts/release.py`

功能：
1. 调用 `build.py` 确保产物是最新的
2. 运行全量 pytest
3. 打包 release zip（`release/doc-based-coding-v{version}.zip`）
4. 内含：双 wheel + INSTALL_GUIDE.md + RELEASE_NOTE.md + README.md
5. 输出 release 摘要与校验信息

### 3. Targeted Tests

- 验证 `build.py --dry-run` 能正确输出构建计划（不实际构建）
- 验证版本一致性检查集成正常

## 验证门

- [x] `scripts/build.py` 能一键完成双包 wheel 构建
- [x] 构建前自动清理旧产物
- [x] 版本一致性检查在构建前自动执行
- [x] wheel 内容物验证通过
- [x] `scripts/release.py` 能一键打包 release zip
- [x] release 前自动运行 pytest
- [x] 全量回归测试通过（823 passed, 2 skipped）

## 不触及

- 远程 CI/CD
- 自动 version bump
- PyPI publishing
- 改变现有包结构或入口
