# Backstage Research

## 产品定位

Backstage 不是 agent 平台，但它是一个成熟的**插件化开发者平台**。它对我们最有价值的是：

- platform vs plugin 的边界
- templates
- docs-like-code

## 关键机制

- Software Templates 可以加载 skeleton、填充变量并发布到 GitHub/GitLab。
- 模板流程包含输入、review page、执行和 success 页。
- TechDocs 是 docs-like-code 方案，文档与代码同仓库维护。
- TechDocs 支持 addon framework。
- TechDocs 还支持与模板、CI/CD、静态生成发布联动。
- Backstage 的整体定位就是 open framework for developer portals，并强调 plugin architecture。

## 对我们最有价值的点

- 平台本体与插件生态可以分离。
- 模板系统不必只是“复制文件”，还可以有 review step。
- docs-like-code 可以成为平台级正式能力，而不是附属文档。

## 与我们目标的差异

- Backstage 不负责 AI intent classification。
- 不负责 subagent orchestration。
- 不直接提供 rule engine 或 HITL agent runtime。

## 对子 agent 管理的启发

直接启发不多，但对 artifact 组织有帮助：

- 模板、docs、addons、actions 应分别建模
- pack 不应只是 prompt 包，也应包含 scaffold / addon / integration 能力

## 我们可吸收的设计点

- platform/plugin 架构
- template review step
- docs-like-code 作为核心能力
- addon 机制

## 当前不应直接照搬的点

- 不应把平台做成重量级 portal
- 不应先做 UI-first，再补规则模型

## 主要来源

- https://backstage.io/docs/features/software-templates/
- https://backstage.io/docs/features/techdocs/
- https://backstage.io/docs/overview/technical-overview
- https://github.com/backstage/backstage
