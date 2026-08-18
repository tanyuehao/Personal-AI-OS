# Personal AI OS V1.0 数据模型设计

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 设计原则

数据模型必须同时支持：
- 业务事实；
- AI 检索；
- Memory；
- 认知变化；
- 完整来源追踪。

任何 AI 生成的结构化认知都必须保存 `source_ref` 与 `confidence`。

## 2. 核心实体

```text
User
 ├─ Document
 │   └─ KnowledgeChunk
 ├─ Conversation
 │   └─ Message
 ├─ Memory
 ├─ Belief
 │   └─ BeliefRevision
 └─ Decision
```

## 3. Memory 模型

字段建议：

```text
id UUID
user_id UUID
type ENUM
content TEXT
summary TEXT
importance FLOAT
confidence FLOAT
status ENUM(candidate, confirmed, rejected, archived)
source_type ENUM(document, conversation, manual, decision)
source_id UUID
embedding VECTOR
created_at
updated_at
last_accessed_at
```

Memory 类型：
- `fact`
- `experience`
- `opinion`
- `decision`
- `preference`

## 4. Belief 与 Memory 的区别

Memory 是“值得长期调用的信息”。

Belief 是“用户在某个主题上的观点状态”，需要版本历史。

```text
belief
  current_statement
  confidence
  topic

belief_revision
  statement
  valid_from
  source
  reason
```

不得直接覆盖旧观点。

## 5. Decision

```text
problem
context
options JSONB
choice
reasoning
risks JSONB
expected_result
actual_result
lesson
status
```

## 6. 数据删除

删除 Document：
1. 标记删除；
2. 删除其 Chunk；
3. 删除/失效对应向量；
4. 找到 source 为该文档的候选 Memory；
5. 重新计算其 evidence；
6. 没有其他来源则归档，而不是静默保留。
