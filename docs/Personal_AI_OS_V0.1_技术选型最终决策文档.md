# Personal AI OS V0.1 技术选型最终决策

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 决策

| 层 | 选择 |
|---|---|
| Backend | Python 3.12 + FastAPI |
| ORM | SQLAlchemy 2.x |
| Schema | Pydantic v2 |
| DB | PostgreSQL 16 |
| Vector | pgvector |
| Migration | Alembic |
| Cache/Queue | Redis |
| Frontend | Next.js + TypeScript |
| Model | DeepSeek via Model Gateway |
| Container | Docker Compose |

## 2. 为什么 V0.1 使用 pgvector

- 减少一个独立服务；
- 数据与向量生命周期更容易保持一致；
- 个人部署足够；
- 后续可引入 Qdrant Adapter。

## 3. DeepSeek

业务层不得绑定具体 SDK。

```text
ChatService -> ModelGateway -> DeepSeekProvider
```

复杂推理与普通生成使用不同 mode，而不是在业务代码散落模型名。

## 4. 暂不选用

### Neo4j
V0.1 数据规模和需求不足，先使用关系表/JSONB。

### Kubernetes
个人开源项目部署成本过高。

### Fine-tuning
当前最重要的是 Memory/RAG 数据闭环，不是训练人格模型。
