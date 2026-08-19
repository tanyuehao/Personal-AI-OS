# Personal AI OS - Create GitHub Releases
# 运行前请先安装 gh CLI: winget install GitHub.cli
# 然后登录: gh auth login

$repo = "tanyuehao/Personal-AI-OS"

$releases = @(
    @{
        tag = "v1.0.0"
        name = "v1.0.0 - Personal AI OS 正式版"
        body = @"
## Personal AI OS V1.0

> Your Data. Your Memory. Your AI.

### 功能清单

| 模块 | 功能 |
|------|------|
| 用户系统 | 注册/登录/Token刷新/数据隔离 |
| 知识库 | 拖拽上传/解析/切片/向量化/语义搜索 |
| AI问答 | RAG/Token budget/引用展示 |
| 记忆系统 | 候选机制/自动提取/评分公式 |
| 认知模型 | 观点管理/时间线/冲突检测/决策关联 |
| Reflection | 重复检测/冲突检测/周报生成 |
| Agent | 4个专业助手 |
| 多模态 | 图片识别/语音转写 |
| 数据导出 | JSON格式 |
| 测试 | 55个测试用例 |
| Docker | 一键部署 |

### 安装

``````bash
git clone https://github.com/tanyuehao/Personal-AI-OS.git
cd Personal-AI-OS
docker-compose up -d
``````

访问 http://localhost:3000
"@
    },
    @{
        tag = "v0.5.0"
        name = "v0.5.0 - 数据导出 + 性能优化"
        body = @"
### 新增功能

- 数据导出（JSON格式）
- 性能优化（数据库索引 + 缓存）
- Docker 部署完善
- 文档同步更新
"@
    },
    @{
        tag = "v0.4.0"
        name = "v0.4.0 - Memory候选 + 时间线 + 测试"
        body = @"
### 新增功能

- Memory 候选机制（PENDING → CONFIRMED/REJECTED）
- 观点时间线可视化
- 知识库搜索过滤器
- 完整测试套件（42个测试）
"@
    },
    @{
        tag = "v0.3.0"
        name = "v0.3.0 - 拖拽上传 + 设置增强"
        body = @"
### 新增功能

- 拖拽上传文件
- AI提供商切换（SiliconFlow/DeepSeek）
- Temperature/Max Tokens设置
- Toast错误提示
"@
    },
    @{
        tag = "v0.2.0"
        name = "v0.2.0 - 记忆集成 + 知识图谱"
        body = @"
### 新增功能

- 记忆集成RAG
- 知识图谱可视化
- 文档自动AI摘要
- 对话删除功能
"@
    },
    @{
        tag = "v0.1.0"
        name = "v0.1.0 - MVP 初版"
        body = @"
### 核心功能

- 用户认证系统
- 文档上传与解析
- AI智能问答（RAG）
- 基础记忆系统
- Agent系统
- 多模态支持
"@
    }
)

foreach ($release in $releases) {
    Write-Host "Creating release $($release.tag)..."
    try {
        gh release create $release.tag `
            --repo $repo `
            --title $release.name `
            --notes $release.body `
            --latest:$($release.tag -eq "v1.0.0")
        Write-Host "  [OK] Created"
    } catch {
        Write-Host "  [FAIL] $($_.Exception.Message)"
    }
}

Write-Host "`nDone! Check: https://github.com/$repo/releases"
