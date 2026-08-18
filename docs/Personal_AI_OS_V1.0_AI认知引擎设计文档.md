# Personal AI OS V1.0 AI 认知引擎设计

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 认知引擎的边界

V0.1 不宣称“复制人格”。认知引擎负责将用户明确表达或有证据支持的信息，组织为可解释、可修改的长期认知资产。

核心原则：

> 事实、用户观点、AI推断三者严格区分。

## 2. 输入

- 用户文档
- 用户主动记录
- 对话
- 决策记录
- 用户对 AI 的纠正

## 3. 输出

- Memory Candidate
- Belief Candidate
- Decision Link
- Conflict Signal

## 4. Memory Pipeline

```text
New content
 -> candidate extraction
 -> classification
 -> evidence linking
 -> deduplication
 -> importance/confidence scoring
 -> candidate storage
 -> user confirmation / passive threshold rule
```

### 推荐评分

```text
score =
0.35 * importance
+ 0.25 * confidence
+ 0.20 * recurrence
+ 0.20 * explicit_user_signal
```

V0.1 不需要复杂 ML，先采用规则 + LLM 判断，可配置。

## 5. 召回策略

Chat 上下文由四部分组成：

1. 当前对话；
2. RAG 文档；
3. confirmed memories；
4. relevant decisions/beliefs。

设独立 token budget，防止 Memory 挤占知识证据。

## 6. 观点演化

如果新观点与旧观点相冲突：

- 不覆盖；
- 创建 revision；
- 记录来源；
- 标记 `possible_change=true`；
- 需要用户确认或多来源证据。

## 7. Reflection

Reflection 不是“AI自我意识”，而是离线整理任务：
- 聚类重复 Memory；
- 检测冲突；
- 建议合并；
- 生成周度认知变化摘要。

## 8. 安全约束

- 不从单次情绪表达推断稳定人格；
- 不根据敏感属性构建不必要画像；
- 任何推断均允许删除；
- Memory 来源必须可追踪。
