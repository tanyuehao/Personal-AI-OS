# Personal AI OS V1.0 后端详细设计

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 技术栈

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16 + pgvector
- Redis
- pytest

## 2. 目录

```text
backend/app/
├── api/
├── core/
├── models/
├── schemas/
├── repositories/
├── services/
├── providers/
├── workers/
└── main.py
```

## 3. 分层约束

### api
HTTP 协议适配，不包含业务规则。

### service
事务编排、业务规则、权限语义。

### repository
数据库 CRUD，禁止调用 LLM。

### provider
外部能力适配：
- deepseek
- embedding
- file storage

## 4. ChatService

职责：
1. 读取 conversation；
2. 调用 Retriever；
3. 调用 MemoryRetriever；
4. 构造 context；
5. Model Gateway；
6. citation validation；
7. persist message；
8. 异步提交 memory extraction。

## 5. Document Processing

Worker 内执行：
- MIME 检测；
- parser；
- normalize；
- chunk；
- embedding；
- transaction 写入；
- 更新状态。

任务必须幂等。重复执行不能产生重复 Chunk。

## 6. Model Gateway

接口示例：

```python
class ModelGateway(Protocol):
    async def chat(self, messages, *, mode, temperature, timeout): ...
```

DeepSeekProvider 实现该协议，业务层不得直接 import SDK。

## 7. 日志

所有请求记录：
- request_id
- user_id
- route
- duration

LLM 记录：
- provider
- model
- duration
- token usage
- error type

禁止日志打印 API Key 和完整敏感文档内容。
