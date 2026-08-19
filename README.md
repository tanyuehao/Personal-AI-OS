<div align="center">

# 🧠 Personal AI OS

### Your Personal Cognitive Operating System — Let AI Be Your Second Brain

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000.svg)](https://nextjs.org/)
[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/tanyuehao/Personal-AI-OS)

[English](#english) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-TW.md)

</div>

---

## What is Personal AI OS?

Personal AI OS is an open-source personal cognitive AI system. It helps AI gradually understand your knowledge base, experience, values, and decision-making patterns through data collection, knowledge comprehension, long-term memory, cognitive modeling, and intelligent agents.

## Core Features

- 📚 **Personal Knowledge Base** — Upload documents with drag & drop, auto-parse, chunk, and vectorize
- 💬 **AI-Powered Q&A** — Answer questions based on your personal knowledge
- 🧠 **Long-term Memory** — Automatically extract and manage important information
- 🔗 **Knowledge Graph** — Interactive visualization of your knowledge connections
- 🎯 **Cognitive Model** — Understand your thinking patterns and decision styles
- 🤖 **AI Agents** — Specialized assistants for business, investment, writing, and review
- 📷 **Multimodal** — Image recognition and voice transcription
- ⚙️ **Flexible Settings** — Switch AI providers, adjust temperature, configure models
- 📊 **Usage Analytics** — Track API usage and rate limits

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + Next.js 14 + Tailwind CSS + Zustand |
| Backend | Python 3.12 + FastAPI + SQLAlchemy |
| Database | PostgreSQL (pgvector) / SQLite + Redis |
| AI Models | DeepSeek / MiMo (SiliconFlow) / OpenAI |

## Quick Start

### Option 1: Docker (Recommended)

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

### Option 2: Local Development

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

## AI Model Configuration

| Provider | Config | Price |
|----------|--------|-------|
| DeepSeek | `AI_PROVIDER=deepseek` | ~¥1/M tokens |
| MiMo (SiliconFlow) | `AI_PROVIDER=siliconflow` | Free tier available |
| OpenAI | `AI_PROVIDER=openai` | Higher cost |

## API Endpoints

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

## Project Structure

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

## Roadmap

- [x] v0.1.0 — MVP: Knowledge base, AI chat, Memory, Agents
- [x] v0.2.0 — Memory integration, Knowledge graph, Auto summarization
- [x] v0.3.0 — Drag upload, Settings enhancement, Toast notifications
- [x] v0.4.0 — Memory candidates, Opinion timeline, Search filters, Test suite
- [x] v0.5.0 — Data export, Performance optimization, Docker deployment
- [x] v1.0.0 — Cognitive engine, Reflection, E2E tests, Security tests
- [x] v1.1.0 — Decision style, Knowledge graph modeling, Memory network, Communication style

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the [Apache License 2.0](LICENSE).

---

<div align="center">

**[Personal AI OS](https://github.com/tanyuehao/Personal-AI-OS)** — Let AI Be Your Second Brain

</div>
