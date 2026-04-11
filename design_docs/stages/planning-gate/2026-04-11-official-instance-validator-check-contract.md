# Planning Gate — Post-v1.0 Official-Instance Validator/Check Contract Closure

- Status: **COMPLETED**
- Date: 2026-04-11

## 问题陈述

双发行包最小安装实现已经完成，但官方实例 `doc-loop-vibe-coding` 在 `validators / checks / scripts` 三个扩展字段上的语义仍有混淆：

1. runtime 当前会把 `manifest.validators` 里的 Python 脚本尝试注册为 pack validators，并在 PEP delegation 后对 `report` 执行校验。
2. runtime 当前会把 `manifest.checks` 里的检查项视为 writeback 前的阻断检查，消费的是 `{"envelope", "result"}` 上下文。
3. 官方实例里的 `validate_doc_loop.py` / `validate_instance_pack.py` 实际验证的是 repo scaffold 与实例包自身，而不是 delegation report 或 writeback 上下文。

这导致当前 manifest 把两个 adoption/self-check 脚本放进 `validators` 后，只能得到“missing-validate”的 skipped 诊断；更重要的是，这个声明本身已经偏离 runtime 对 validator 的真实消费语义。

## 审核后边界

用户已确认：下一切片先做“官方实例 validator/check 契约收口”，优先级高于兼容元数据声明。

本轮边界固定为：

- 只澄清并收口 `validators / checks / scripts` 的边界
- 只修正官方实例 manifest 与相关文档/测试/诊断
- 不在本轮实现通用 `checks` 字段直连能力
- 不在本轮引入新的 manifest 字段
- 不在本轮重做 script-style validator 的完整长期协议

## 权威输入

- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/Project Master Checklist.md`
- `docs/pack-manifest.md`
- `docs/first-stable-release-boundary.md`
- `src/pack/registrar.py`
- `src/pep/executor.py`
- `doc-loop-vibe-coding/pack-manifest.json`
- `tests/test_extension_bridging.py`

## 本轮只做什么

### Slice A: 字段消费边界文档化

- 把 `validators`、`checks`、`scripts` 在 runtime 中各自消费什么输入明确写入权威文档。
- 明确 adoption/self-check 命令默认属于 `scripts`，不应因“名字像 validate”而自动归入 runtime validator。

### Slice B: 官方实例 manifest 收口

- 修正 `doc-loop-vibe-coding/pack-manifest.json` 中的字段归属。
- 确保官方实例不再把 scaffold / instance self-check 脚本错误声明为 runtime validators。

### Slice C: 诊断与测试对齐

- 更新相关诊断与测试断言，使其反映新的字段边界。
- 确认官方实例不再产生无意义的 `missing-validate` skipped 诊断。

## 本轮明确不做什么

- 不新增通用 report-style validator 示例
- 不把 `validate_doc_loop.py` / `validate_instance_pack.py` 硬改造成 delegation report validator
- 不实现 checks 字段的官方实例新用法
- 不进入 compatibility metadata slice

## 验收与验证门

- `docs/pack-manifest.md` 明确三类字段的消费边界
- 官方实例 manifest 不再把 adoption/self-check 脚本放进 `validators`
- 针对官方实例的 registrar / pipeline 诊断不再报告这两个脚本为 `missing-validate`
- 相关 targeted tests 通过

## 执行结果

- `docs/pack-manifest.md` 已补齐 `validators / checks / scripts` 的 runtime 消费边界说明。
- `doc-loop-vibe-coding/pack-manifest.json` 已移除误归类的 `validators` 声明，并停止把 self-check 脚本作为 runtime validators 提供。
- `src/pack/registrar.py` 注释已明确：CLI/self-check/bootstrap 脚本应留在 `scripts` 字段，而不是 `validators`。
- `tests/test_extension_bridging.py` 与 `tests/test_official_instance_e2e.py` 已按新边界更新断言。
- targeted tests 已通过；fresh `Pipeline.info()` 读取下，官方实例不再产生 `missing-validate` skipped 诊断。

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `.codex/checkpoints/latest.md`
- `docs/pack-manifest.md`

## 收口判断

- 当边界文档、官方实例 manifest、诊断与测试都已对齐时，本切片即可收口。
- 收口后再决定是否继续进入“兼容元数据与版本声明”切片。