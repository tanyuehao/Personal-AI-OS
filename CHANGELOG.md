# Changelog

本文件记录 Personal AI OS 的所有版本变更。

## [1.0.0] - 2026-08-18

### Added
- 认知引擎：Belief 自动提取、冲突检测、决策关联
- Reflection 离线整理：重复检测、冲突检测、周报生成
- LLM 超时重试机制（RetryAIService）
- 文档处理幂等性
- E2E 测试（5 个端到端场景）
- 安全测试（8 个安全测试）
- Token budget 控制（知识 3000 + 记忆 1000）
- 记忆评分公式
- GitHub Actions CI/CD
- Docker Hub 自动发布

### Changed
- 改进 RAG 引用展示
- 优化系统提示词

## [0.5.0] - 2026-08-18

### Added
- 数据导出功能（JSON 格式）
- 性能优化（数据库复合索引 + 内存缓存）
- Docker 部署完善（docker-compose + .env.example）
- 文档同步更新

## [0.4.0] - 2026-08-18

### Added
- Memory 候选机制（PENDING → CONFIRMED/REJECTED）
- 观点时间线可视化
- 知识库搜索过滤器
- 完整测试套件（42 个测试）

### Fixed
- 登录页面默认填充测试账号
- 修复路由顺序问题

## [0.3.0] - 2026-08-18

### Added
- 拖拽上传文件
- AI 提供商切换（SiliconFlow / DeepSeek）
- Temperature/Max Tokens 设置
- Toast 错误提示

## [0.2.0] - 2026-08-18

### Added
- 记忆集成 RAG
- 知识图谱可视化
- 文档自动 AI 摘要
- 对话删除功能

## [0.1.0] - 2026-08-18

### Added
- 用户认证系统
- 文档上传与解析
- AI 智能问答（RAG）
- 基础记忆系统
- Agent 系统
- 多模态支持
- Docker 部署
