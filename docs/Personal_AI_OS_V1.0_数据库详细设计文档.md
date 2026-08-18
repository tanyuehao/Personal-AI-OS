# Personal AI OS V1.0 数据库详细设计

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 技术基线

- PostgreSQL 16
- pgvector
- Alembic migration
- Redis 7（缓存/任务状态）
- 原始文件：本地目录，后续可替换 MinIO/S3

## 2. 表清单

### users
- id UUID PK
- email CITEXT UNIQUE
- password_hash
- created_at
- updated_at

### documents
- id UUID PK
- user_id FK
- filename
- mime_type
- storage_path
- sha256
- status
- parser_version
- created_at

索引：`(user_id, created_at desc)`、`sha256`

### knowledge_chunks
- id UUID PK
- document_id FK
- user_id FK
- chunk_index
- content
- token_count
- metadata JSONB
- embedding VECTOR
- created_at

索引：
- `(document_id, chunk_index)`
- `(user_id)`
- vector ANN index

### conversations / messages
消息保存 role、content、model、token usage、citations JSONB。

### memories
保存 type、content、importance、confidence、status、source。

### beliefs / belief_revisions
保存观点当前态和历史版本。

### decisions
保存决策完整生命周期。

## 3. 多用户隔离

所有用户数据表必须直接或间接带 `user_id`，Repository 查询必须默认加入用户条件。

禁止：
```sql
SELECT * FROM documents WHERE id = :id;
```

必须：
```sql
SELECT * FROM documents
WHERE id = :id AND user_id = :user_id;
```

## 4. Migration 规范

- 禁止手工修改生产表结构；
- 每个 schema 变化必须生成 Alembic migration；
- destructive migration 必须提供回滚/备份说明；
- Release 前执行空库和旧库升级测试。

## 5. 备份

至少备份：
- PostgreSQL；
- 原始文件；
- 配置模板（不含密钥）。

向量可从 Chunk 重建，但生产环境仍建议随数据库备份。
