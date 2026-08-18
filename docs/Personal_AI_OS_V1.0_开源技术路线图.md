# Personal AI OS 开源技术路线图

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## v0.1 Alpha：Knowledge Brain

- DeepSeek Model Gateway
- Document Pipeline
- pgvector RAG
- Chat + Citation
- Basic Memory

## v0.2：Reliable Memory

- candidate/confirmed lifecycle
- dedupe
- confidence
- evidence
- Memory UI

## v0.3：Cognitive Timeline

- beliefs
- belief revisions
- decisions
- conflict detection

## v0.4：Connectors

- local folder watcher
- Markdown/Obsidian
- mail/export connector（根据社区需求）

## v1.0 Stable

稳定：
- 安装
- 升级
- 备份
- Memory
- RAG
- 数据导出
- 文档/API

## v2.x

在基础稳定后探索：
- Agents
- multi-modal
- knowledge graph
- local model optimization
