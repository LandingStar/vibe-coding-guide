# Planning Gate — Pack Index Metadata & CLI Pack Management

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-13-pack-index-and-cli-management |
| Scope | Pack Index 格式定义 + CLI `pack` 子命令 + platform.json 扩展 |
| Status | **COMPLETED** |
| 来源 | `design_docs/plugin-distribution-marketplace-direction-analysis.md` 方案 A、`docs/plugin-model.md` §Pack Origins |
| 前置 | pack discovery、site-packages auto-discovery 已稳定 |
| 测试基线 | 803 passed, 2 skipped |

## 问题陈述

当前 pack 的安装/管理只有两条路径：

1. 手动复制 pack 目录到项目内（convention scan 发现）
2. `pip install` Python wheel 包（site-packages auto-discovery）

缺少：
- 用户友好的 CLI 命令来安装、列举、移除 pack
- 标准化的 pack 交换格式（pack index / 元数据）
- `platform.json` 对 pack 来源的显式管理

## 目标

**做**：
1. 定义 `pack-index.json` 元数据格式（name / version / kind / runtime_compatibility / path / checksum）
2. CLI 新增 `doc-based-coding pack` 子命令族：`list` / `install` / `remove` / `info <name>`
3. `pack install <path>` 从本地路径复制 pack 到 `.codex/packs/` 并注册到 `platform.json`
4. `pack list` 列出所有已发现的 pack（convention + site-packages + explicit config）
5. `pack remove <name>` 从 `.codex/packs/` 移除并更新 `platform.json`
6. 更新 `docs/plugin-model.md` Pack Origins 章节

**不做**：
- 远程 index URL / 网络下载
- SQLite 本地 registry（方案 B）
- 版本约束解析 / 多版本共存
- MCP pack 管理工具（可后续扩展）
- 改变 `_discover_packs()` 核心逻辑

## 交付物

### 1. Pack Index 格式（`docs/pack-index-format.md`）

轻量 JSON 格式，描述单个 pack 的元数据：

```json
{
  "name": "my-pack",
  "version": "1.0.0",
  "kind": "project-local",
  "runtime_compatibility": ">=0.9.2,<1.0.0",
  "path": ".codex/packs/my-pack",
  "checksum": "sha256:..."
}
```

### 2. CLI `pack` 子命令（`src/__main__.py` 扩展）

| 命令 | 说明 |
|------|------|
| `doc-based-coding pack list` | 列出所有已发现的 pack |
| `doc-based-coding pack install <path>` | 从本地路径安装 pack 到 `.codex/packs/` |
| `doc-based-coding pack remove <name>` | 移除已安装的 pack |
| `doc-based-coding pack info <name>` | 显示指定 pack 的详细信息 |

### 3. platform.json 扩展

`pack_dirs` 字段在 `pack install` 时自动更新：

```json
{
  "pack_dirs": [
    ".codex/packs/my-pack",
    "doc-loop-vibe-coding"
  ]
}
```

### 4. Pack 安装逻辑（`src/pack/pack_manager.py`）

- `install_pack(source_path, project_root)` → 复制 manifest + 资产到 `.codex/packs/<name>/`
- `remove_pack(name, project_root)` → 删除目录 + 从 platform.json 移除
- `list_packs(project_root)` → 调用 `_discover_packs()` 返回格式化列表

### 5. Targeted Tests

- `pack install` 从本地路径安装 → 目录存在 + platform.json 更新
- `pack list` 返回所有已发现 pack
- `pack remove` 删除后不再被发现
- `pack info` 显示 manifest 字段

## 验证门

- [x] `pack-index.json` 格式文档化 → `docs/pack-index-format.md`
- [x] `doc-based-coding pack list` 列出 convention + site-packages + config packs
- [x] `doc-based-coding pack install <path>` 正确复制并注册
- [x] `doc-based-coding pack remove <name>` 正确移除并更新 config
- [x] `doc-based-coding pack info <name>` 显示 manifest 内容
- [x] targeted tests 全部通过 — 20 tests in `tests/test_pack_manager.py`
- [x] 全量回归测试通过 — 823 passed, 2 skipped

## 不触及

- 远程 index / 网络下载
- SQLite 本地 registry
- 版本约束解析
- MCP pack 管理工具
- `_discover_packs()` 核心逻辑改动
