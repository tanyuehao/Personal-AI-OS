# Personal AI OS V1.0 部署运维文档

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. V0.1 推荐部署

Docker Compose：

```text
frontend
backend
worker
postgres
redis
```

pgvector 运行在 PostgreSQL 中，减少组件数量。

## 2. 环境变量

```env
APP_ENV=production
DATABASE_URL=
REDIS_URL=
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=
FILE_STORAGE_PATH=/data/files
SECRET_KEY=
```

必须提供 `.env.example`，不得提交真实 `.env`。

## 3. 数据目录

建议：
```text
/data/
  postgres/
  files/
  backups/
```

## 4. 健康检查

- `/health/live`
- `/health/ready`

Ready 需要检查数据库；无需每次检查 DeepSeek，以免外部故障导致整个服务被摘除。

## 5. Backup

每日：
- pg_dump
- files 增量/快照

恢复演练至少每个重要 Release 一次。

## 6. Upgrade

```text
backup
 -> pull image
 -> run migration
 -> start services
 -> smoke test
 -> rollback if needed
```

## 7. 日志与监控

关注：
- parse failed rate
- model error rate
- queue backlog
- DB disk
- request latency

V0.1 无需引入复杂 Kubernetes。
