# Personal AI OS V1.0 API 接口设计

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. API 约定

Base URL：`/api/v1`

统一响应：

```json
{
  "data": {},
  "error": null,
  "request_id": "uuid"
}
```

错误：
```json
{
  "data": null,
  "error": {
    "code": "DOCUMENT_PARSE_FAILED",
    "message": "..."
  },
  "request_id": "uuid"
}
```

## 2. Authentication

- `POST /auth/register`
- `POST /auth/login`
- `GET /me`

## 3. Documents

- `POST /documents`
- `GET /documents`
- `GET /documents/{id}`
- `DELETE /documents/{id}`
- `POST /documents/{id}/reprocess`

上传成功只表示任务已接受，不表示索引完成。

状态：
`UPLOADED -> PROCESSING -> READY | FAILED`

## 4. Chat

`POST /chat`

请求：
```json
{
  "conversation_id": "uuid|null",
  "message": "string",
  "knowledge_scope": [],
  "memory_enabled": true,
  "mode": "normal|reasoning"
}
```

返回至少包含：
- answer
- citations
- conversation_id
- model
- usage

## 5. Memory

- `GET /memories`
- `POST /memories`
- `PATCH /memories/{id}`
- `DELETE /memories/{id}`
- `POST /memories/{id}/confirm`
- `POST /memories/{id}/reject`

AI 自动提取默认生成 `candidate`，不得直接视为确认事实。

## 6. Decisions

- `POST /decisions`
- `GET /decisions`
- `GET /decisions/{id}`
- `PATCH /decisions/{id}`
- `POST /decisions/{id}/review`

## 7. 任务

文档解析等长任务：
- `GET /tasks/{id}`

## 8. 错误码

- AUTH_REQUIRED
- FORBIDDEN
- NOT_FOUND
- VALIDATION_ERROR
- DOCUMENT_PARSE_FAILED
- EMBEDDING_FAILED
- MODEL_TIMEOUT
- MODEL_RATE_LIMIT
- VECTOR_SEARCH_FAILED

HTTP status 与业务 error code 同时使用。
