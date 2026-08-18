# Personal AI OS V0.1 工程师执行任务清单

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## Backend

- [ ] 创建 settings/config
- [ ] Auth middleware
- [ ] User repository/service
- [ ] Document CRUD
- [ ] Upload validation
- [ ] Parser abstraction
- [ ] Chunker
- [ ] Embedding provider
- [ ] pgvector repository
- [ ] Retrieval service
- [ ] Chat service
- [ ] DeepSeek provider
- [ ] Conversation persistence
- [ ] Memory CRUD
- [ ] Memory candidate extractor
- [ ] Background worker
- [ ] Health endpoints

## Frontend

- [ ] App shell
- [ ] Login
- [ ] Knowledge list
- [ ] Upload component
- [ ] Processing status
- [ ] Chat UI
- [ ] Citation panel
- [ ] Memory review
- [ ] Decision form
- [ ] Settings/model status

## QA

- [ ] Unit test
- [ ] API test
- [ ] RAG test set
- [ ] Memory test set
- [ ] Migration test
- [ ] E2E smoke
- [ ] Docker clean-install test

## Release

- [ ] README
- [ ] .env.example
- [ ] LICENSE
- [ ] CHANGELOG
- [ ] Docker images
- [ ] Tag `v0.1.0-alpha`
