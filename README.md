<div align="center">

# 🧠 Personal AI OS

### 個人認知操作系統 — 讓 AI 成為你的第二大腦

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000.svg)](https://nextjs.org/)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/tanyuehao/Personal-AI-OS)

[English](#english) | [简体中文](#简体中文) | [繁體中文](#繁體中文)

</div>

---

## English

### What is Personal AI OS?

Personal AI OS is an open-source personal cognitive AI system. It helps AI gradually understand your knowledge base, experience, values, and decision-making patterns through data collection, knowledge comprehension, long-term memory, cognitive modeling, and intelligent agents.

### Core Features

- 📚 **Personal Knowledge Base** — Upload documents, auto-parse, chunk, and vectorize
- 💬 **AI-Powered Q&A** — Answer questions based on your personal knowledge
- 🧠 **Long-term Memory** — Automatically extract and manage important information
- 🎯 **Cognitive Model** — Understand your thinking patterns and decision styles
- 🤖 **AI Agents** — Specialized assistants for business, investment, writing, and review
- 📷 **Multimodal** — Image recognition and voice transcription
- 📊 **Usage Analytics** — Track API usage and rate limits

### Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + Next.js 14 + Tailwind CSS + Zustand |
| Backend | Python 3.12 + FastAPI + SQLAlchemy |
| Database | PostgreSQL (pgvector) / SQLite + Redis |
| AI Models | DeepSeek / MiMo (SiliconFlow) / OpenAI |

### Quick Start

#### Option 1: Docker (Recommended)

```bash
git clone https://github.com/tanyuehao/Personal-AI-OS.git
cd Personal-AI-OS

# Configure environment
cp backend/.env.example backend/.env
# Edit .env with your API key

# Start services
docker-compose up -d

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### Option 2: Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### AI Model Configuration

| Provider | Config | Price |
|----------|--------|-------|
| DeepSeek | `AI_PROVIDER=deepseek` | ~¥1/M tokens |
| MiMo (SiliconFlow) | `AI_PROVIDER=siliconflow` | Free tier available |
| OpenAI | `AI_PROVIDER=openai` | Higher cost |

### API Endpoints

| Module | Endpoint | Description |
|--------|----------|-------------|
| Auth | `POST /api/v1/auth/register` | User registration |
| Auth | `POST /api/v1/auth/login` | User login |
| Documents | `POST /api/v1/documents/upload` | Upload documents |
| Knowledge | `POST /api/v1/knowledge/search` | Semantic search |
| Chat | `POST /api/v1/ai/chat` | AI conversation |
| Memory | `POST /api/v1/memory` | Create memories |
| Beliefs | `POST /api/v1/cognitive/beliefs` | Manage beliefs |
| Decisions | `POST /api/v1/decision` | Record decisions |
| Agent | `POST /api/v1/agent/run` | Run AI agents |

### Project Structure

```
Personal-AI-OS/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes (12 modules)
│   │   ├── core/           # Config, security, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   └── requirements.txt
├── frontend/               # Next.js frontend
│   ├── app/                # 14 pages
│   ├── components/         # React components
│   ├── services/           # API client
│   └── stores/             # Zustand state
├── docs/                   # Design documents (23 docs)
└── docker-compose.yml      # Docker deployment
```

### Roadmap

- [x] v0.1.0 — MVP: Knowledge base, AI chat, Memory, Agents
- [ ] v0.2.0 — Auto memory extraction, RAG memory integration
- [ ] v0.3.0 — Knowledge graph, Auto summarization
- [ ] v1.0.0 — Full cognitive model, Decision engine

### Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### License

This project is licensed under the [Apache License 2.0](LICENSE).

---

## 简体中文

### 什么是 Personal AI OS？

Personal AI OS 是一个开源的个人认知 AI 系统。通过数据采集、知识理解、长期记忆、认知建模和智能代理技术，让 AI 逐步理解你的知识体系、经验、价值观和决策方式。

### 核心功能

- 📚 **个人知识库** — 上传文档，自动解析、切片、向量化
- 💬 **AI 智能问答** — 基于你的个人资料进行回答
- 🧠 **长期记忆** — 自动提取和管理重要信息
- 🎯 **认知模型** — 理解你的思维方式和决策模式
- 🤖 **AI Agent** — 专业助手帮你完成复杂任务
- 📷 **多模态** — 图片识别和语音转写
- 📊 **使用量统计** — 追踪 API 使用情况和速率限制

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Next.js 14 + Tailwind CSS + Zustand |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy |
| 数据库 | PostgreSQL (pgvector) / SQLite + Redis |
| AI 模型 | DeepSeek / MiMo (SiliconFlow) / OpenAI |

### 快速开始

#### 方式一：Docker 部署（推荐）

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

#### 方式二：本地开发

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

### AI 模型配置

| 提供商 | 配置 | 价格 |
|--------|------|------|
| DeepSeek | `AI_PROVIDER=deepseek` | 约 ¥1/百万 tokens |
| MiMo (SiliconFlow) | `AI_PROVIDER=siliconflow` | 有免费额度 |
| OpenAI | `AI_PROVIDER=openai` | 较贵 |

### API 接口

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

### 项目结构

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

### 开发路线

- [x] v0.1.0 — MVP：知识库、AI 问答、记忆、Agent
- [ ] v0.2.0 — 记忆自动提取、RAG 集成记忆
- [ ] v0.3.0 — 知识图谱、自动总结
- [ ] v1.0.0 — 完整认知模型、决策引擎

### 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。

---

## 繁體中文

### 什麼是 Personal AI OS？

Personal AI OS 是一個開源的個人認知 AI 系統。透過資料蒐集、知識理解、長期記憶、認知建模和智慧代理技術，讓 AI 逐步理解你的知識體系、經驗、價值觀和決策方式。

### 核心功能

- 📚 **個人知識庫** — 上傳文件，自動解析、分片、向量化
- 💬 **AI 智慧問答** — 基於你的個人資料進行回答
- 🧠 **長期記憶** — 自動擷取和管理重要資訊
- 🎯 **認知模型** — 理解你的思維方式和決策模式
- 🤖 **AI Agent** — 專業助手幫你完成複雜任務
- 📷 **多模態** — 圖片辨識和語音轉寫
- 📊 **使用量統計** — 追蹤 API 使用情況和速率限制

### 技術棧

| 層級 | 技術 |
|------|------|
| 前端 | React + Next.js 14 + Tailwind CSS + Zustand |
| 後端 | Python 3.12 + FastAPI + SQLAlchemy |
| 資料庫 | PostgreSQL (pgvector) / SQLite + Redis |
| AI 模型 | DeepSeek / MiMo (SiliconFlow) / OpenAI |

### 快速開始

#### 方式一：Docker 部署（建議）

```bash
git clone https://github.com/tanyuehao/Personal-AI-OS.git
cd Personal-AI-OS

# 設定環境變數
cp backend/.env.example backend/.env
# 編輯 .env 檔案，填入你的 API Key

# 啟動服務
docker-compose up -d

# 存取應用
# 前端：http://localhost:3000
# 後端 API：http://localhost:8000
# API 文件：http://localhost:8000/docs
```

#### 方式二：本地開發

```bash
# 後端
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

### AI 模型設定

| 供應商 | 設定 | 價格 |
|--------|------|------|
| DeepSeek | `AI_PROVIDER=deepseek` | 約 ¥1/百萬 tokens |
| MiMo (SiliconFlow) | `AI_PROVIDER=siliconflow` | 有免費額度 |
| OpenAI | `AI_PROVIDER=openai` | 較貴 |

### API 介面

| 模組 | 介面 | 說明 |
|------|------|------|
| 認證 | `POST /api/v1/auth/register` | 使用者註冊 |
| 認證 | `POST /api/v1/auth/login` | 使用者登入 |
| 文件 | `POST /api/v1/documents/upload` | 上傳文件 |
| 知識庫 | `POST /api/v1/knowledge/search` | 語意搜尋 |
| 聊天 | `POST /api/v1/ai/chat` | AI 對話 |
| 記憶 | `POST /api/v1/memory` | 建立記憶 |
| 觀點 | `POST /api/v1/cognitive/beliefs` | 管理觀點 |
| 決策 | `POST /api/v1/decision` | 記錄決策 |
| Agent | `POST /api/v1/agent/run` | 執行 Agent |

### 專案結構

```
Personal-AI-OS/
├── backend/                 # Python FastAPI 後端
│   ├── app/
│   │   ├── api/            # API 路由（12 個模組）
│   │   ├── core/           # 設定、安全、資料庫
│   │   ├── models/         # 資料模型
│   │   ├── schemas/        # 請求回應模型
│   │   └── services/       # 業務邏輯
│   └── requirements.txt
├── frontend/               # Next.js 前端
│   ├── app/                # 14 個頁面
│   ├── components/         # React 元件
│   ├── services/           # API 客戶端
│   └── stores/             # Zustand 狀態管理
├── docs/                   # 設計文件（23 份）
└── docker-compose.yml      # Docker 部署
```

### 開發路線

- [x] v0.1.0 — MVP：知識庫、AI 問答、記憶、Agent
- [ ] v0.2.0 — 記憶自動擷取、RAG 整合記憶
- [ ] v0.3.0 — 知識圖譜、自動總結
- [ ] v1.0.0 — 完整認知模型、決策引擎

### 貢獻

歡迎貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解詳情。

### 授權條款

本專案採用 [Apache License 2.0](LICENSE) 授權條款。

---

<div align="center">

**[Personal AI OS](https://github.com/tanyuehao/Personal-AI-OS)** — 讓 AI 成為你的第二大腦

</div>
