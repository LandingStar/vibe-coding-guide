# Pack Index Format

> 权威来源：`docs/pack-index-format.md`
> 版本：0.9.2

## 概述

Pack Index 是一组轻量 JSON 元数据，描述单个 pack 的身份和安装状态。CLI `pack list` / `pack info` 命令输出即遵循此格式。

## 字段定义

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| `name` | string | ✓ | pack 唯一标识符（与 `pack-manifest.json` 中 `name` 一致） |
| `version` | string | ✓ | 语义化版本号 |
| `kind` | string | ✓ | pack 类型：`platform` / `official-instance` / `project-local` |
| `source` | string | ✓ | 发现来源：`config` / `convention` / `site-packages` / `installed` |
| `path` | string | ✓ | pack 根目录的路径 |
| `manifest_path` | string | ✓ | `pack-manifest.json` 文件的完整路径 |
| `runtime_compatibility` | string | | 运行时版本兼容范围（如 `>=0.9.2,<1.0.0`） |
| `provides` | string[] | | pack 提供的能力列表（如 `["rules", "intents", "gates"]`） |

## Source 值含义

| source | 含义 |
|--------|------|
| `installed` | 通过 `pack install` 安装到 `.codex/packs/`，由 `platform.json` 管理 |
| `config` | 在 `.codex/platform.json` `pack_dirs` 显式注册，但位于 `.codex/packs/` 之外 |
| `convention` | 项目根目录下子目录中发现（convention scan） |
| `site-packages` | 通过 `pip install` 安装到 Python 环境的 site-packages |

## 示例

### 单个 pack 信息（`pack info` 输出）

```json
{
  "name": "doc-loop-vibe-coding",
  "version": "0.9.2",
  "kind": "official-instance",
  "source": "site-packages",
  "path": "/path/to/site-packages/doc_loop_vibe_coding",
  "manifest_path": "/path/to/site-packages/doc_loop_vibe_coding/pack-manifest.json",
  "runtime_compatibility": ">=0.9.2,<1.0.0",
  "provides": ["rules", "document_types", "prompts", "intents", "gates", "triggers"]
}
```

### platform.json 中的 pack 注册

```json
{
  "pack_dirs": [
    ".codex/packs/my-custom-pack",
    "doc-loop-vibe-coding"
  ]
}
```

`pack install` 会自动向 `pack_dirs` 追加路径；`pack remove` 会自动移除。

## 与 pack-manifest.json 的关系

Pack Index 是 `pack-manifest.json` 的**运行时投影**——它包含 manifest 中的核心字段加上运行时发现信息（`source`、解析后的绝对路径）。`pack-manifest.json` 是 pack 作者维护的源文件，Pack Index 是平台运行时生成的元数据视图。
