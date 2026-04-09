# Subagent Delegation Standard

## 文档定位

本文件定义 `{{PROJECT_NAME}}` 中主 agent 与子 agent 的默认协作边界。

## 适用范围

当任务需要并行工作、局部探索或切换会话接手时，应使用本标准收紧 delegation 范围。

## 责任边界

默认责任如下：

- 主 agent 负责 planning、权威文档、集成、验证策略与最终 write-back
- 子 agent 负责被明确授权的窄切片
- 共享状态文档与 handoff 默认由主 agent 维护

## 委派合同

每份子 agent 合同至少应说明：

- 任务目标
- 允许修改的文件范围
- 必须重读的正式文档
- 验收标准
- 需要运行的验证
- 明确不做什么

## 回收与写回

子 agent 返回时，应优先提交：

- 改动事实
- 运行过的验证
- 未解决问题
- 不确定项与假设

最终是否写入长期文档，由主 agent 统一裁决。

## 幻觉防线

为了降低多 agent 漂移：

- 子 agent 不自行扩 scope
- 子 agent 不擅自改写项目阶段口径
- 子 agent 摘要不等于已验证事实
- 若发现 planning doc 与代码现实冲突，应先升级给主 agent

## 当前边界

本标准只约束 delegation 方式，不替代具体阶段文档与业务设计文档。
