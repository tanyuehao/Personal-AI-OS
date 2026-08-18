# Personal AI OS 开源贡献者指南

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 贡献优先级

欢迎：
- bug fix
- parser
- retrieval
- evaluation
- Memory quality
- docs
- deployment
- provider adapters

## 2. 开发步骤

```bash
git clone ...
cp .env.example .env
docker compose up -d postgres redis
# backend/frontend 按仓库说明启动
```

## 3. Issue

Bug 必须包含：
- 版本/commit；
- OS；
- 安装方式；
- 复现步骤；
- expected / actual；
- sanitized log。

## 4. PR

一个 PR 尽量解决一个问题。涉及 schema/API 时必须同步文档和测试。

## 5. AI 生成代码

允许使用 DeepSeek 等工具，但提交者必须：
- 理解代码；
- 运行测试；
- 不提交虚构 API；
- 检查许可证/复制来源；
- 对最终代码负责。
