# Personal AI OS

**个人认知操作系统** - 让 AI 成为你的第二大脑

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

## 📋 项目简介

Personal AI OS 是一个开源的个人认知 AI 系统，通过数据采集、知识理解、长期记忆、认知建模和智能代理技术，让 AI 逐步理解你的知识体系、经验、价值观和决策方式。

### 核心功能

- 🗂️ **个人知识库** - 上传文档，自动解析、分片、向量化
- 💬 **AI 智能问答** - 基于你的个人资料进行回答
- 🧠 **长期记忆** - 自动提取和管理重要信息
- 📊 **认知模型** - 理解你的思维方式和决策模式
- 🤖 **AI Agent** - 专业助手帮你完成复杂任务

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+ (LTS)
- PostgreSQL 16+
- Redis 7+

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/your-username/Personal-AI-OS.git
cd Personal-AI-OS

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env 文件，填入你的 API Key（见下方模型配置）

# 启动服务
docker-compose up -d

# 访问应用
# 前端：http://localhost:3000
# 后端 API：http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 方式二：本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 🤖 模型配置

本项目支持多种 AI 模型，推荐使用 **DeepSeek**（便宜好用）或 **小米 MiMo**（有免费额度）。

### 推荐配置：DeepSeek（最便宜）

| 模型 | 价格 | 说明 |
|------|------|------|
| deepseek-chat | ¥1/百万 tokens（输入）¥2/百万 tokens（输出）| 通用对话 |
| deepseek-coder | ¥1/百万 tokens（输入）¥2/百万 tokens（输出）| 代码专用 |

**注册地址**：https://platform.deepseek.com/

**配置方式**：
```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
```

### 备选配置：小米 MiMo（有免费额度）

通过 SiliconFlow 平台调用，新用户有免费额度。

**注册地址**：https://siliconflow.cn/

**配置方式**：
```env
AI_PROVIDER=mimo
MIMO_API_KEY=sk-your-siliconflow-api-key
```

### 其他支持的模型

| 提供商 | 配置项 | 价格 |
|--------|--------|------|
| OpenAI | OPENAI_API_KEY | 较贵 |
| 本地模型 | LOCAL_MODEL_ENABLED=true | 免费（需 GPU）|

### 自动降级

设置 `AI_PROVIDER=auto` 可以启用自动降级，系统会按优先级尝试多个模型：
```env
AI_PROVIDER=auto
MODEL_PRIORITY=deepseek,mimo,openai,local
```

## 📁 项目结构

```
Personal-AI-OS/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 接口
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # 请求响应模型
│   │   ├── services/       # 业务逻辑
│   │   ├── ai/             # AI 能力模块
│   │   ├── memory/         # 记忆模块
│   │   └── agents/         # Agent 模块
│   └── alembic/            # 数据库迁移
├── frontend/               # 前端应用
├── ai-engine/              # AI 引擎
├── memory-engine/          # 记忆引擎
├── knowledge-engine/       # 知识引擎
├── database/               # 数据库脚本
├── devops/                 # 部署配置
└── docs/                   # 项目文档
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Next.js + Tailwind CSS |
| 后端 | Python + FastAPI |
| 数据库 | PostgreSQL + pgvector |
| 缓存 | Redis |
| AI | OpenAI / DeepSeek / Qwen |

## 📚 文档

- [PRD 产品需求文档](docs/Personal_AI_OS_V1.0_PRD完整版.docx)
- [系统架构设计](docs/Personal_AI_OS_V1.0_系统架构设计文档.docx)
- [API 接口文档](docs/Personal_AI_OS_V1.0_API接口设计文档.docx)

## 🤝 贡献

欢迎贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。

## 🙏 致谢

感谢所有贡献者和开源社区的支持！
