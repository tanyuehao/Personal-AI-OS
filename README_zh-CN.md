<div align="center">

# 🧠 Personal AI OS

### 个人认知操作系统 — 让 AI 成为你的第二大脑

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000.svg)](https://nextjs.org/)
[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](https://github.com/tanyuehao/Personal-AI-OS)

[English](README.md) | [简体中文](#简体中文) | [繁體中文](README_zh-TW.md)

</div>

---

## 什么是 Personal AI OS？

Personal AI OS 是一个开源的个人认知 AI 系统。通过数据采集、知识理解、长期记忆、认知建模和智能代理技术，让 AI 逐步理解你的知识体系、经验、价值观和决策方式。

## 核心功能

- 📚 **个人知识库** — 拖拽上传文档，自动解析、切片、向量化
- 💬 **AI 智能问答** — 基于你的个人资料进行回答
- 🧠 **长期记忆** — 自动提取和管理重要信息
- 🔗 **知识图谱** — 可视化知识关联关系
- 🎯 **认知模型** — 理解你的思维方式和决策模式
- 🤖 **AI Agent** — 专业助手帮你完成复杂任务
- 📷 **多模态** — 图片识别和语音转写
- ⚙️ **灵活设置** — 切换 AI 提供商，调整温度参数，配置模型
- 📊 **使用量统计** — 追踪 API 使用情况和速率限制

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Next.js 14 + Tailwind CSS + Zustand |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy |
| 数据库 | PostgreSQL (pgvector) / SQLite + Redis |
| AI 模型 | DeepSeek / MiMo (SiliconFlow) / OpenAI |

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
git clone https://github.com/tanyuehao/Personal-AI-OS.git
cd Personal-AI-OS

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env 文件，填入你的 API Key

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

## AI 模型配置

| 提供商 | 配置 | 价格 |
|--------|------|------|
| DeepSeek | `AI_PROVIDER=deepseek` | 约 ¥1/百万 tokens |
| MiMo (SiliconFlow) | `AI_PROVIDER=siliconflow` | 有免费额度 |
| OpenAI | `AI_PROVIDER=openai` | 较贵 |

## API 接口

| 模块 | 接口 | 说明 |
|------|------|------|
| 认证 | `POST /api/v1/auth/register` | 用户注册 |
| 认证 | `POST /api/v1/auth/login` | 用户登录 |
| 文档 | `POST /api/v1/documents/upload` | 上传文档 |
| 知识库 | `POST /api/v1/knowledge/search` | 语义搜索 |
| 聊天 | `POST /api/v1/ai/chat` | AI 对话 |
| 记忆 | `POST /api/v1/memory` | 创建记忆 |
| 观点 | `POST /api/v1/cognitive/beliefs` | 管理观点 |
| 决策 | `POST /api/v1/decision` | 记录决策 |
| Agent | `POST /api/v1/agent/run` | 运行 Agent |

## 项目结构

```
Personal-AI-OS/
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由（12 个模块）
│   │   ├── core/           # 配置、安全、数据库
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # 请求响应模型
│   │   └── services/       # 业务逻辑
│   └── requirements.txt
├── frontend/               # Next.js 前端
│   ├── app/                # 14 个页面
│   ├── components/         # React 组件
│   ├── services/           # API 客户端
│   └── stores/             # Zustand 状态管理
├── docs/                   # 设计文档（23 份）
└── docker-compose.yml      # Docker 部署
```

## 开发路线

- [x] v0.1.0 — MVP：知识库、AI 问答、记忆、Agent
- [x] v0.2.0 — 记忆集成、知识图谱、自动摘要
- [x] v0.3.0 — 拖拽上传、设置增强、Toast 提示
- [x] v0.4.0 — Memory 候选、观点时间线、搜索过滤、测试套件
- [ ] v0.5.0 — 数据导出、性能优化
- [ ] v1.0.0 — 完整认知模型、决策引擎

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。

---

<div align="center">

**[Personal AI OS](https://github.com/tanyuehao/Personal-AI-OS)** — 让 AI 成为你的第二大脑

</div>
