# Planning Gate: Pack Manager 预留接口实现

- Gate ID: `2026-04-17-pack-manager-reserved-interfaces`
- Scope: `src/pack/pack_manager.py` + 对应测试
- Parent Checklist Item: 风险条目 "runtime_compatibility 仅存储未校验 + _compute_checksum 未被调用"

## 目标

将 `pack_manager.py` 中的两个预留接口补充为可用实现：

1. **runtime_compatibility 校验**：install_pack 时检查 pack 声明的 runtime_compatibility 是否与当前 platform version 兼容
2. **manifest checksum 记录**：install_pack 时计算并存储 manifest 的 SHA-256 checksum 到 platform.json

## Slice 定义

### Slice A: runtime_compatibility 校验

- 新增 `_get_runtime_version() -> str`：从 `importlib.metadata` 读取当前包版本，回退到 `pyproject.toml` 解析
- 新增 `_check_runtime_compatibility(specifier: str, runtime_version: str) -> bool`：使用 `packaging.specifiers.SpecifierSet` 校验兼容性
- `install_pack()` 在复制文件前调用校验，不兼容时 raise `ValueError` 并给出明确消息
- 行为选择：**hard reject**（不兼容直接拒绝安装），因为允许安装不兼容 pack 会导致运行时不可预期行为

### Slice B: manifest checksum 记录

- `install_pack()` 在安装完成后计算已安装 manifest 的 `_compute_checksum()`
- 将 checksum 存储到 `platform.json` 的 `pack_checksums: { pack_name: checksum_str }` 字段
- `get_pack_info()` / `list_packs()` 返回的 `PackInfo` 中暴露 checksum
- 暂不做运行时完整性校验（可作为后续 planning-gate）

### 测试

- runtime_compatibility 校验通过 / 拒绝 / 空值跳过
- checksum 记录 / 读回 / PackInfo 暴露
- 整合到 `test_pack_manager_boundary.py`

## 依赖

- `packaging` 库（PEP 440 版本比较）— 检查是否已在 requirements.txt

## 验收条件

- [x] 不兼容 pack install 抛出 ValueError
- [x] 兼容 pack install 正常完成
- [x] 空 runtime_compatibility 跳过校验
- [x] platform.json 记录 checksum
- [x] PackInfo.checksum 字段可用
- [x] 全量回归无降级（1058 passed, 2 skipped）
