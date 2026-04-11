# Execute By Doc Prompt

先读当前 active planning 或 phase 文档，再开始实现。

实施要求：

- 只处理文档声明的当前切片
- 若发现新问题超出当前边界，写回 open items 或 planning-gate
- 代码、测试、帮助、文档同步必须围绕同一个切片
- 不要把未验证内容写成完成

若实施途中需要用户做选择、审批、方向确认或下一步取舍：

- 先陈述你当前的分析与推荐
- 再用 askQuestions 或推进式提问继续交流
- 不要用阶段性总结把对话停住

完成后请准备 write-back，而不是只给口头总结。
