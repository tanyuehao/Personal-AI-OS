# Personal AI OS V0.1 第一版代码框架设计

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 建议单仓库

```text
Personal-AI-OS/
├── backend/
├── frontend/
├── docs/
├── docker/
├── scripts/
├── tests/
├── docker-compose.yml
└── .env.example
```

V0.1 不建议把 `ai-engine`、`memory-engine` 等拆成多个独立 Python 包/服务，先作为 Backend 内清晰模块：

```text
backend/app/
├── api/
├── services/
│   ├── chat.py
│   ├── documents.py
│   ├── retrieval.py
│   └── memories.py
├── ai/
│   ├── gateway.py
│   ├── providers/deepseek.py
│   ├── prompts/
│   └── evaluation/
├── knowledge/
│   ├── parser/
│   ├── chunker.py
│   └── embeddings.py
├── memory/
│   ├── extractor.py
│   ├── ranking.py
│   └── retriever.py
└── ...
```

## 2. 原则

- 逻辑模块化，不等于部署微服务化；
- 所有 provider 可替换；
- Service 不直接写 SQL；
- Repository 不调用 AI；
- Prompt 版本化；
- AI 输出必须经 schema 校验。

## 3. 第一条垂直功能

优先实现完整 vertical slice：

`upload -> index -> chat -> citation`

再开始 Memory，避免同时铺开所有模块。
