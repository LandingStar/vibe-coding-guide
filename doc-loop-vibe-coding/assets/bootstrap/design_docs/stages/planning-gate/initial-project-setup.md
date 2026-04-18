# Planning Gate: {{PROJECT_NAME}} 初始化

- created: {{CURRENT_DATE}}
- status: active
- scope: initial-project-setup

## 目标

完成 {{PROJECT_NAME}} 的首次文档驱动工作流初始化。

## 验证门

- [ ] `doc-based-coding validate` 无阻塞项
- [ ] 确认项目的第一个真实工作切片方向

## 下一步

当验证通过后，创建你的第一个真实 planning-gate 替换本文件：

```bash
# 示例：创建一个具体的工作切片 planning-gate
# 文件名格式：YYYY-MM-DD-<scope>.md
```

## 备注

本文件由 `bootstrap_doc_loop` 自动生成，用于满足 C5 约束（必须有活跃 planning-gate）。
当你开始真正的工作切片时，应创建新的 planning-gate 文档并将本文件标记为 `status: completed`。
