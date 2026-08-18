# Personal AI OS V1.0 系统架构设计

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 架构目标

- 单机优先，避免 V0.1 过度微服务化；
- 模块边界清晰，可在未来拆服务；
- AI Provider 可替换；
- 原始数据、向量、Memory 全部可追溯；
- AI 推断与业务事实分离。

## 2. V0.1 逻辑架构

```text
Browser / Desktop
       |
     Next.js
       |
  FastAPI Backend
       |
 +-----+-----------+------------+
 |                 |            |
Document        RAG/Chat      Memory
Service         Service       Service
 |                 |            |
Parser/Chunk   Retriever    Extract/Rank
 |                 |            |
 +------ PostgreSQL + pgvector --+
                   |
              Model Gateway
                   |
               DeepSeek
```

## 3. 模块职责

### Backend API
只负责认证、参数校验、调用 Service、返回 DTO。禁止在 Router 写复杂业务。

### Document Service
- 文件元数据；
- 解析任务；
- Chunk 生命周期；
- 删除级联。

### Knowledge Engine
- Chunking；
- Embedding；
- Hybrid/Vector Retrieval；
- Citation 生成。

### Model Gateway
统一模型调用接口：
- chat
- reasoning
- embedding（若采用外部 embedding provider）
- timeout / retry / rate limit
- usage logging

### Memory Engine
- 候选记忆提取；
- 去重；
- 打分；
- 用户确认；
- 召回。

### Cognitive Engine
V0.1 仅提供轻量能力：
- 观点聚合；
- 观点冲突检测；
- 决策历史召回。
不进行“人格复制”或自动训练。

## 4. 关键调用链

### 文档导入
```text
POST /documents
 -> persist metadata
 -> enqueue parse task
 -> parser
 -> chunker
 -> embedding
 -> vector index
 -> status=READY
```

### Chat
```text
POST /chat
 -> auth
 -> query normalization
 -> retrieve knowledge
 -> retrieve memories
 -> context budget
 -> DeepSeek
 -> citation validation
 -> persist messages
 -> optional memory candidate extraction
```

## 5. 故障隔离

- 文档解析失败不影响 API；
- DeepSeek 不可用时返回明确 provider error；
- 向量索引失败时任务可重试；
- Memory 提取失败不得影响用户拿到聊天答案。

## 6. 未来演进

只有在以下条件满足后才拆微服务：
- 单体服务成为部署瓶颈；
- 独立模块需要不同扩缩容；
- 社区贡献导致模块独立维护需求明显。
