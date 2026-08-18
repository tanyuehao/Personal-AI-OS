# Personal AI OS V1.0 测试方案与质量保障

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 测试层级

- Unit
- Integration
- API
- RAG evaluation
- Memory evaluation
- End-to-End
- Security
- Upgrade/Migration

## 2. 核心 E2E

### E2E-01
上传一份文档 -> READY -> 提问 -> 回答包含正确 citation。

### E2E-02
用户表达明确偏好 -> 生成 candidate memory -> 用户确认 -> 新会话可召回。

### E2E-03
删除文档 -> 不再检索到其 Chunk -> 来源 Memory 被重新评估。

## 3. RAG 指标

测试集每条包含：
- question
- expected_sources
- required_facts
- forbidden_claims

评估：
- Recall@K
- Citation precision
- Answer groundedness
- Unsupported claim rate

## 4. Memory 指标

- Candidate precision
- Duplicate rate
- Incorrect type rate
- Unsupported memory rate
- Retrieval relevance

V0.1 宁可少记，不可乱记。

## 5. 性能

基线环境记录硬件配置。
- API P95
- Retrieval P95
- 文档处理吞吐
- LLM timeout rate

## 6. 安全

- 越权访问；
- 路径穿越；
- 恶意文件类型；
- Prompt injection 文档；
- Secret 泄露；
- 日志敏感信息。

## 7. Release Gate

以下任一失败不得发布：
- 数据隔离；
- Migration；
- 文档删除级联；
- Citation 基础准确性；
- Memory 可删除；
- API Key 不泄露。
