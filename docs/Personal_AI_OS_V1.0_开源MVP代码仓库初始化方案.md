# Personal AI OS V1.0 开源 MVP 仓库初始化方案

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 首次初始化必须包含

```text
README.md
LICENSE
CONTRIBUTING.md
CODE_OF_CONDUCT.md
SECURITY.md
CHANGELOG.md
.env.example
docker-compose.yml
backend/
frontend/
docs/
.github/
```

## 2. GitHub 配置

- Issues
- Discussions
- Pull Request template
- Bug report template
- Feature request template
- CI checks

## 3. Milestone

### v0.1.0-alpha
- boot
- document pipeline
- RAG chat
- citations
- basic memory

## 4. First Issues

1. bootstrap backend
2. bootstrap frontend
3. docker postgres/redis
4. DeepSeek ModelGateway
5. document upload
6. parser/chunker
7. pgvector retrieval
8. chat/citation
9. memory candidate
10. clean install test

## 5. 发布原则

Alpha 也必须可安装、可回滚、可清理数据，不发布只在开发者机器上能跑的版本。
