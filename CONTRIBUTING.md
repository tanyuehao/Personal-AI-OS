<div align="center">

# Contributing to Personal AI OS

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

[English](#english) | [简体中文](#简体中文) | [繁體中文](#繁體中文)

</div>

---

## English

### Welcome

We welcome contributions from the community! Whether it's bug reports, feature requests, documentation improvements, or code contributions, every help is appreciated.

### How to Contribute

#### 1. Fork the Repository

```bash
# Fork on GitHub, then clone
git clone https://github.com/your-username/Personal-AI-OS.git
cd Personal-AI-OS
git remote add upstream https://github.com/tanyuehao/Personal-AI-OS.git
```

#### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

#### 3. Make Changes

- Follow the existing code style
- Write clear commit messages
- Add tests if applicable
- Update documentation if needed

#### 4. Commit

```bash
git add .
git commit -m "feat: add new feature"  # or "fix: fix bug"
```

**Commit Message Convention:**

| Prefix | Description |
|--------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation changes |
| `style:` | Code style changes (formatting, etc.) |
| `refactor:` | Code refactoring |
| `test:` | Adding tests |
| `chore:` | Maintenance tasks |

#### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

### Development Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Code Style

#### Python

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Keep functions focused and short

#### TypeScript/React

- Use functional components with hooks
- Follow ESLint rules
- Use TypeScript types properly
- Keep components small and focused

### Reporting Bugs

When reporting bugs, please include:

1. **Description** — Clear description of the issue
2. **Steps to reproduce** — How to reproduce the problem
3. **Expected behavior** — What you expected to happen
4. **Actual behavior** — What actually happened
5. **Environment** — OS, Python version, Node.js version
6. **Screenshots** — If applicable

### Feature Requests

We welcome feature requests! Please:

1. Check if the feature already exists
2. Describe the use case
3. Explain why it would be valuable
4. Consider implementation details

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's coding standards

### Questions?

If you have questions, feel free to open an issue or reach out to the maintainers.

---

## 简体中文

### 欢迎贡献

我们欢迎社区的贡献！无论是 Bug 报告、功能请求、文档改进还是代码贡献，都感谢你的帮助。

### 如何贡献

#### 1. Fork 仓库

```bash
# 在 GitHub 上 Fork，然后克隆
git clone https://github.com/your-username/Personal-AI-OS.git
cd Personal-AI-OS
git remote add upstream https://github.com/tanyuehao/Personal-AI-OS.git
```

#### 2. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

#### 3. 修改代码

- 遵循现有代码风格
- 编写清晰的提交信息
- 添加测试（如适用）
- 更新文档（如需要）

#### 4. 提交

```bash
git add .
git commit -m "feat: 添加新功能"  # 或 "fix: 修复 bug"
```

**提交信息规范：**

| 前缀 | 说明 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | Bug 修复 |
| `docs:` | 文档变更 |
| `style:` | 代码格式变更 |
| `refactor:` | 代码重构 |
| `test:` | 添加测试 |
| `chore:` | 维护任务 |

#### 5. 推送并创建 PR

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

### 开发环境搭建

#### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

### 代码规范

#### Python

- 遵循 PEP 8
- 使用类型注解
- 为公共函数编写文档字符串
- 保持函数专注且简短

#### TypeScript/React

- 使用函数组件和 Hooks
- 遵循 ESLint 规则
- 正确使用 TypeScript 类型
- 保持组件小而专注

### 报告 Bug

报告 Bug 时，请包含：

1. **描述** — 清晰描述问题
2. **复现步骤** — 如何复现问题
3. **期望行为** — 你期望发生什么
4. **实际行为** — 实际发生了什么
5. **环境** — 操作系统、Python 版本、Node.js 版本
6. **截图** — 如适用

### 功能请求

我们欢迎功能请求！请：

1. 检查功能是否已存在
2. 描述使用场景
3. 解释为什么有价值
4. 考虑实现细节

### 行为准则

- 尊重和包容
- 专注于建设性反馈
- 帮助他人学习和成长
- 遵循项目的编码标准

### 有问题？

如果有问题，欢迎提 Issue 或联系维护者。

---

## 繁體中文

### 歡迎貢獻

我們歡迎社群的貢獻！無論是 Bug 報告、功能請求、文件改進還是程式碼貢獻，都感謝你的幫助。

### 如何貢獻

#### 1. Fork 倉庫

```bash
# 在 GitHub 上 Fork，然後克隆
git clone https://github.com/your-username/Personal-AI-OS.git
cd Personal-AI-OS
git remote add upstream https://github.com/tanyuehao/Personal-AI-OS.git
```

#### 2. 建立分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

#### 3. 修改程式碼

- 遵循現有程式碼風格
- 編寫清晰的提交訊息
- 新增測試（如適用）
- 更新文件（如需要）

#### 4. 提交

```bash
git add .
git commit -m "feat: 新增功能"  # 或 "fix: 修復 bug"
```

**提交訊息規範：**

| 前綴 | 說明 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | Bug 修復 |
| `docs:` | 文件變更 |
| `style:` | 程式碼格式變更 |
| `refactor:` | 程式碼重構 |
| `test:` | 新增測試 |
| `chore:` | 維護任務 |

#### 5. 推送並建立 PR

```bash
git push origin feature/your-feature-name
```

然後在 GitHub 上建立 Pull Request。

### 開發環境搭建

#### 後端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

### 程式碼規範

#### Python

- 遵循 PEP 8
- 使用型別註解
- 為公共函數編寫文件字串
- 保持函數專注且簡短

#### TypeScript/React

- 使用函數元件和 Hooks
- 遵循 ESLint 規則
- 正確使用 TypeScript 型別
- 保持元件小而專注

### 報告 Bug

報告 Bug 時，請包含：

1. **描述** — 清晰描述問題
2. **重現步驟** — 如何重現問題
3. **期望行為** — 你期望發生什麼
4. **實際行為** — 實際發生了什麼
5. **環境** — 作業系統、Python 版本、Node.js 版本
6. **截圖** — 如適用

### 功能請求

我們歡迎功能請求！請：

1. 檢查功能是否已存在
2. 描述使用場景
3. 解釋為什麼有價值
4. 考慮實作細節

### 行為準則

- 尊重和包容
- 專注於建設性回饋
- 幫助他人學習和成長
- 遵循專案的編碼標準

### 有問題？

如果有問題，歡迎提 Issue 或聯絡維護者。
