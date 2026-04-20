# User-Global Config

用户级全局配置，跨工作区生效。

## 配置文件位置

```
~/.doc-based-coding/config.json
```

可通过环境变量 `DOC_BASED_CODING_USER_DIR` 覆盖基目录：

```bash
export DOC_BASED_CODING_USER_DIR=/custom/path
# → /custom/path/config.json
```

## 字段说明

```json
{
  "extra_pack_dirs": ["/path/to/shared-packs", "~/other-packs"],
  "default_model": "claude-opus-4",
  "default_llm_params": {
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `extra_pack_dirs` | `string[]` | `[]` | 额外的 pack 发现目录（追加到内置路径列表，不替换） |
| `default_model` | `string \| null` | `null` | 默认 LLM 模型标识符（项目级配置可覆盖） |
| `default_llm_params` | `object` | `{}` | 默认 LLM 参数（如 temperature、max_tokens 等） |

所有字段均为可选。未知字段被静默忽略（前向兼容）。

## 降级行为

以下场景均不报错，使用空默认值：

- `~/.doc-based-coding/` 目录不存在
- `config.json` 文件不存在
- `config.json` 内容不是有效 JSON
- 字段类型不匹配（如 `extra_pack_dirs` 为字符串而非数组）

## 与 Pack 系统的关系

- `extra_pack_dirs` 中发现的 pack 与 `~/.doc-based-coding/packs/` 中的 pack 一起作为用户级 pack 参与合并
- 合并优先级：`platform-default(0) < official-instance(1) < user-global(2) < project-local(3)`
- 项目级 pack 始终胜出

## 跨平台行为

| OS | 默认路径 |
|----|---------|
| Windows | `%USERPROFILE%\.doc-based-coding\config.json` |
| macOS | `~/.doc-based-coding/config.json` |
| Linux | `~/.doc-based-coding/config.json` |

所有平台统一使用 `Path.home()` 解析。

## Pipeline API

`Pipeline.info()` 返回值中包含 `user_config` 节（仅当 `include_user_global=True` 且配置非空时）：

```json
{
  "user_config": {
    "extra_pack_dirs": ["/path/to/shared-packs"],
    "default_model": "claude-opus-4",
    "default_llm_params": {"temperature": 0.7}
  }
}
```
