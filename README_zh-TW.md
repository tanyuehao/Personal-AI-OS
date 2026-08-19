<div align="center">

# 🧠 Personal AI OS

### 個人認知操作系統 — 讓 AI 成為你的第二大腦

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000.svg)](https://nextjs.org/)
[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/tanyuehao/Personal-AI-OS)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](#繁體中文)

</div>

---

## 什麼是 Personal AI OS？

Personal AI OS 是一個開源的個人認知 AI 系統。透過資料蒐集、知識理解、長期記憶、認知建模和智慧代理技術，讓 AI 逐步理解你的知識體系、經驗、價值觀和決策方式。

## 核心功能

- 📚 **個人知識庫** — 拖曳上傳文件，自動解析、分片、向量化
- 💬 **AI 智慧問答** — 基於你的個人資料進行回答
- 🧠 **長期記憶** — 自動擷取和管理重要資訊
- 🔗 **知識圖譜** — 視覺化知識關聯關係
- 🎯 **認知模型** — 理解你的思維方式和決策模式
- 🤖 **AI Agent** — 專業助手幫你完成複雜任務
- 📷 **多模態** — 圖片辨識和語音轉寫
- ⚙️ **靈活設定** — 切換 AI 供應商，調整溫度參數，設定模型
- 📊 **使用量統計** — 追蹤 API 使用情況和速率限制

## 技術棧

| 層級 | 技術 |
|------|------|
| 前端 | React + Next.js 14 + Tailwind CSS + Zustand |
| 後端 | Python 3.12 + FastAPI + SQLAlchemy |
| 資料庫 | PostgreSQL (pgvector) / SQLite + Redis |
| AI 模型 | DeepSeek / MiMo (SiliconFlow) / OpenAI |

## 快速開始

### 方式一：Docker 部署（建議）

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

### 方式二：本地開發

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

## AI 模型設定

| 供應商 | 設定 | 價格 |
|--------|------|------|
| DeepSeek | `AI_PROVIDER=deepseek` | 約 ¥1/百萬 tokens |
| MiMo (SiliconFlow) | `AI_PROVIDER=siliconflow` | 有免費額度 |
| OpenAI | `AI_PROVIDER=openai` | 較貴 |

## API 介面

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

## 專案結構

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

## 開發路線

- [x] v0.1.0 — MVP：知識庫、AI 問答、記憶、Agent
- [x] v0.2.0 — 記憶整合、知識圖譜、自動摘要
- [x] v0.3.0 — 拖曳上傳、設定增強、Toast 提示
- [x] v0.4.0 — Memory 候選、觀點時間線、搜尋過濾、測試套件
- [x] v0.5.0 — 資料匯出、效能優化、Docker 部署
- [x] v1.0.0 — 認知引擎、Reflection、E2E 測試、安全測試
- [x] v1.1.0 — 決策風格、知識圖譜建模、記憶網路、溝通風格

## 貢獻

歡迎貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解詳情。

## 授權條款

本專案採用 [Apache License 2.0](LICENSE) 授權條款。

---

<div align="center">

**[Personal AI OS](https://github.com/tanyuehao/Personal-AI-OS)** — 讓 AI 成為你的第二大腦

</div>
