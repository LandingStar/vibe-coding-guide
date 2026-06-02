如果要让这个 VS Code Chat 真正支持 **vibe coding**，核心是：让 AI 不只是聊天，而是能“看项目、改代码、跑命令、看结果、继续迭代”。

建议添加这些工具能力：

---

## 1. 工作区读取工具

### 功能
让 AI 能查看当前项目内容。

### 需要能力
- 获取工作区根目录
- 列出目录文件
- 读取文件内容
- 读取多个文件
- 获取文件元信息

### 典型用途
- 理解项目结构
- 分析 README、package.json、配置文件
- 找入口文件
- 判断技术栈和项目目标

### 示例工具
```ts
readFile(path)
listFiles(path)
getWorkspaceRoot()
```

---

## 2. 代码搜索工具

### 功能
让 AI 能在项目中快速查找符号、文本、引用。

### 需要能力
- 全局文本搜索
- 按文件名搜索
- 查找函数/类/变量定义
- 查找引用关系

### 典型用途
- “这个接口在哪里定义？”
- “登录逻辑在哪？”
- “谁调用了这个函数？”
- “帮我改所有相关地方”

### 示例工具
```ts
searchText(query, include?, exclude?)
findFiles(pattern)
findReferences(symbol)
```

---

## 3. 文件编辑工具

### 功能
让 AI 能直接修改代码。

### 需要能力
- 创建文件
- 修改文件
- 删除文件
- 按范围替换
- 应用 patch/diff
- 多文件批量修改

### 典型用途
- 实现新功能
- 修 bug
- 重构代码
- 添加配置文件
- 更新文档

### 示例工具
```ts
writeFile(path, content)
editFile(path, edits)
applyPatch(diff)
deleteFile(path)
```

---

## 4. 终端命令工具

### 功能
让 AI 能执行命令并读取输出。

### 需要能力
- 运行 shell 命令
- 获取 stdout/stderr
- 获取退出码
- 支持工作目录
- 支持超时控制

### 典型用途
- 安装依赖
- 启动项目
- 执行测试
- 构建项目
- 查看 Git 状态
- 复现报错

### 示例工具
```ts
runCommand(command, cwd?, timeout?)
```

---

## 5. 诊断信息工具

### 功能
让 AI 读取 VS Code / TypeScript / ESLint 等诊断结果。

### 需要能力
- 获取当前文件诊断
- 获取整个工作区诊断
- 获取错误、警告、类型错误

### 典型用途
- 修复 TypeScript 报错
- 修复 ESLint 问题
- 根据编译错误定位问题
- 改完代码后自动验证

### 示例工具
```ts
getDiagnostics(file?)
```

---

## 6. Git 工具

### 功能
让 AI 了解代码变更状态。

### 需要能力
- 查看当前分支
- 查看 git status
- 查看 diff
- 查看提交历史
- 可选：创建 commit

### 典型用途
- 总结本次修改
- 检查改动是否合理
- 生成 commit message
- 防止误改无关文件

### 示例工具
```ts
gitStatus()
gitDiff()
gitLog(limit)
gitCommit(message)
```

---

## 7. 测试工具

### 功能
让 AI 能运行并分析测试。

### 需要能力
- 运行全部测试
- 运行指定测试
- 获取失败用例信息
- 获取覆盖率信息

### 典型用途
- TDD 开发
- 修 bug 后验证
- 根据失败测试继续修改

### 示例工具
```ts
runTests()
runTestFile(path)
getTestResults()
```

---

## 8. 项目任务/脚本识别工具

### 功能
自动识别项目能怎么运行。

### 需要能力
- 读取 package.json scripts
- 读取 Makefile
- 读取 pyproject.toml
- 读取 docker-compose.yml
- 推断启动、测试、构建命令

### 典型用途
- “帮我启动项目”
- “这个项目怎么跑？”
- “自动执行构建验证”

---

## 9. 文档上下文工具

### 功能
支持 doc-based coding，让 AI 能优先基于项目文档回答。

### 需要能力
- 索引 README、docs、注释
- 向量检索或关键词检索
- 返回相关文档片段
- 标注来源文件

### 典型用途
- 根据项目规范写代码
- 遵守架构文档
- 回答项目设计问题
- 找 API 使用说明

### 示例工具
```ts
searchDocs(query)
getRelevantContext(query)
```

---

## 10. 用户确认与安全控制

### 功能
避免 AI 直接执行危险操作。

### 建议机制
以下操作执行前需要用户确认：

- 删除文件
- 覆盖大量文件
- 执行 `rm -rf`
- 执行安装依赖
- 执行网络请求
- Git commit / push
- 修改配置、环境变量
- 数据库迁移

### 典型策略
```ts
requiresApproval: true
```

---

# 最小可用工具组合

如果想先做一个可用版本，建议优先实现这 5 个：

1. `listFiles`
2. `readFile`
3. `searchText`
4. `editFile` / `applyPatch`
5. `runCommand`

有了这几个，AI 基本就能完成：

- 看项目
- 找代码
- 改代码
- 跑测试
- 根据结果继续修

---

# 完整 vibe coding 流程

理想情况下流程是这样：

```text
用户：帮我加一个登录接口

AI：
1. 读取项目结构
2. 查找路由、控制器、服务层
3. 阅读相关代码
4. 制定修改计划
5. 修改代码
6. 添加测试
7. 运行测试
8. 读取报错
9. 修复问题
10. 总结改动
```

这才是真正的 vibe coding，而不是单纯“生成一段代码”。

---

# 推荐工具能力分级

## Level 1：只读分析型

- 读取文件
- 列目录
- 搜索代码

适合：
- 项目分析
- 解释代码
- 写文档
- 定位问题

---

## Level 2：可修改代码型

- 文件编辑
- patch 应用
- 新建文件
- 删除文件

适合：
- 修 bug
- 写功能
- 重构
- 生成测试

---

## Level 3：可验证执行型

- 运行终端命令
- 运行测试
- 获取诊断
- 获取构建结果

适合：
- 自动迭代开发
- 编译修复
- 测试驱动开发

---

## Level 4：工程协作型

- Git diff
- Git status
- commit message
- 文档检索
- 任务规划
- 安全确认

适合：
- 长任务开发
- PR 辅助
- 自动总结变更
- 团队规范开发

---

# 建议最终工具列表

可以设计成这样：

```ts
getWorkspaceRoot()
listFiles(path)
readFile(path)
writeFile(path, content)
editFile(path, edits)
applyPatch(diff)
deleteFile(path)

searchText(query, options)
findFiles(pattern)

runCommand(command, options)
getDiagnostics(path?)

gitStatus()
gitDiff()
gitLog(limit)

runTests(options)

searchDocs(query)
```

---

总结一下：

如果你想让这个 Chat 支持 vibe coding，最关键的不是模型本身，而是给它接入这些能力：

> **读项目 + 搜代码 + 改文件 + 跑命令 + 看错误 + 继续迭代**

先实现 `readFile / listFiles / searchText / editFile / runCommand`，就能达到一个比较实用的版本。
