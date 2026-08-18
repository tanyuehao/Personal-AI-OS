# Personal AI OS V1.0 开发实施计划与 Sprint 拆解

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 实施策略

以 V0.1 可运行闭环为第一目标，不为未来功能提前建设复杂平台。

## 2. Sprint 0：工程基线

- 仓库整理
- Docker Compose
- FastAPI/Next.js
- PostgreSQL/pgvector
- Alembic
- CI
- DeepSeek Provider stub

完成标准：一条命令启动开发环境。

## 3. Sprint 1：Document Pipeline

- 上传
- MIME validation
- parser
- chunk
- embedding
- status
- deletion

完成标准：文档 READY 后能检索到 Chunk。

## 4. Sprint 2：RAG Chat

- Retriever
- prompt
- DeepSeek gateway
- conversation
- citation

完成标准：标准问题集可正确引用来源。

## 5. Sprint 3：Memory

- schema
- candidate extractor
- user review
- retrieval
- chat integration

完成标准：确认后的 Memory 能在新会话中召回。

## 6. Sprint 4：Decision + Hardening

- decision CRUD
- test suite
- migration test
- security
- backup
- docs

## 7. Definition of Done

一个任务只有同时满足以下条件才完成：
- 代码；
- 测试；
- 文档；
- 错误处理；
- Review；
- 可在干净环境运行。
