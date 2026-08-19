# ============================================
# Personal AI OS - 一键发布脚本
# ============================================
# 用法: .\scripts\release.ps1 [版本号]
# 示例: .\scripts\release.ps1 1.1.0
#       .\scripts\release.ps1 patch   # 自动递增补丁版本
#       .\scripts\release.ps1 minor   # 自动递增次版本
#       .\scripts\release.ps1 major   # 自动递增主版本

param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

# ============================================
# 配置
# ============================================
$REPO = "tanyuehao/Personal-AI-OS"
$PROJECT_DIR = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# ============================================
# 函数
# ============================================

function Write-Step {
    param([string]$Step, [string]$Message)
    Write-Host ""
    Write-Host "[$Step] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "  [FAIL] $Message" -ForegroundColor Red
}

function Get-CurrentVersion {
    # 从 package.json 读取版本
    $packageJson = Get-Content "$PROJECT_DIR\frontend\package.json" | ConvertFrom-Json
    return $packageJson.version
}

function Update-Version {
    param([string]$NewVersion)
    
    # 更新 frontend/package.json
    $packageJson = Get-Content "$PROJECT_DIR\frontend\package.json" -Raw | ConvertFrom-Json
    $packageJson.version = $NewVersion
    $packageJson | ConvertTo-Json -Depth 10 | Set-Content "$PROJECT_DIR\frontend\package.json"
    
    # 更新后端 config.py
    $configPath = "$PROJECT_DIR\backend\app\core\config.py"
    $config = Get-Content $configPath -Raw
    $config = $config -replace 'APP_VERSION: str = "[^"]*"', "APP_VERSION: str = `"$NewVersion`""
    Set-Content $configPath $config -NoNewline
    
    Write-Success "版本号已更新为 $NewVersion"
}

function Test-Build {
    Write-Step "1" "运行测试..."
    
    Set-Location "$PROJECT_DIR\backend"
    
    # 检查 pytest 是否安装
    $pytest = & "venv\Scripts\python.exe" -m pytest --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        & "venv\Scripts\python.exe" -m pip install pytest pytest-asyncio httpx --quiet
    }
    
    # 运行测试
    $result = & "venv\Scripts\python.exe" -m pytest tests/ -v --tb=short 2>&1
    $result | Out-File "$PROJECT_DIR\test_output.log"
    
    if ($result -match "(\d+) passed") {
        $passed = $matches[1]
        Write-Success "测试通过: $passed 个用例"
        return $true
    } else {
        Write-Error "测试失败"
        $result | Select-String -Pattern "FAILED|ERROR" | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        return $false
    }
}

function Build-Frontend {
    Write-Step "2" "构建前端..."
    
    Set-Location "$PROJECT_DIR\frontend"
    
    # 清理旧构建
    if (Test-Path ".next") {
        Remove-Item -Recurse -Force ".next"
    }
    
    # 构建
    $result = & npm run build 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "前端构建成功"
        return $true
    } else {
        Write-Error "前端构建失败"
        return $false
    }
}

function Create-Commit {
    param([string]$Version)
    
    Write-Step "3" "创建提交..."
    
    Set-Location $PROJECT_DIR
    
    git add -A
    git commit -m "release: v$Version" 2>&1 | Out-Null
    
    Write-Success "提交已创建"
}

function Create-Tag {
    param([string]$Version)
    
    Write-Step "4" "创建 Tag v$Version..."
    
    Set-Location $PROJECT_DIR
    
    $tagMessage = Get-TagMessage $Version
    git tag -a "v$Version" -m $tagMessage 2>&1 | Out-Null
    
    Write-Success "Tag v$Version 已创建"
}

function Get-TagMessage {
    param([string]$Version)
    
    $major, $minor, $patch = $Version.Split('.')
    
    # 读取当前变更日志
    $changelog = ""
    $logFile = "$PROJECT_DIR\CHANGELOG.md"
    if (Test-Path $logFile) {
        $content = Get-Content $logFile -Raw
        if ($content -match "## \[?$Version\]?.*?\n([\s\S]*?)(?=\n## |\z)") {
            $changelog = $matches[1].Trim()
        }
    }
    
    if (-not $changelog) {
        $changelog = "Release v$Version"
    }
    
    return $changelog
}

function Push-Changes {
    param([string]$Version)
    
    Write-Step "5" "推送到 GitHub..."
    
    Set-Location $PROJECT_DIR
    
    # 推送提交
    git push origin main 2>&1 | Out-Null
    Write-Success "提交已推送"
    
    # 推送 Tag
    git push origin "v$Version" 2>&1 | Out-Null
    Write-Success "Tag 已推送"
}

function Create-GitHubRelease {
    param([string]$Version)
    
    Write-Step "6" "创建 GitHub Release..."
    
    Set-Location $PROJECT_DIR
    
    # 检查 gh CLI 是否可用
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if ($gh) {
        $releaseBody = Get-ReleaseBody $Version
        $releaseBody | Out-File "$PROJECT_DIR\release_body.md" -Encoding utf8
        
        try {
            gh release create "v$Version" `
                --repo $REPO `
                --title "v$Version" `
                --notes-file "$PROJECT_DIR\release_body.md" `
                --latest
            Write-Success "GitHub Release 已创建"
        } catch {
            Write-Error "GitHub Release 创建失败: $($_.Exception.Message)"
            Write-Host "  请手动创建: https://github.com/$REPO/releases/new" -ForegroundColor Yellow
        }
        
        Remove-Item "$PROJECT_DIR\release_body.md" -ErrorAction SilentlyContinue
    } else {
        Write-Host "  gh CLI 未安装，跳过自动创建 Release" -ForegroundColor Yellow
        Write-Host "  请手动创建: https://github.com/$REPO/releases/new" -ForegroundColor Yellow
    }
}

function Get-ReleaseBody {
    param([string]$Version)
    
    return @"
## v$Version

### 更新内容

详见 [CHANGELOG.md](CHANGELOG.md)

### 安装

``````bash
git clone https://github.com/$REPO.git
cd Personal-AI-OS
docker-compose up -d
``````

访问 http://localhost:3000
"@
}

function Show-Summary {
    param([string]$Version)
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  发布完成! v$Version" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  GitHub: https://github.com/$REPO"
    Write-Host "  Releases: https://github.com/$REPO/releases/tag/v$Version"
    Write-Host "  Docker Hub: https://hub.docker.com/r/$REPO"
    Write-Host ""
    Write-Host "  下一步:" -ForegroundColor Yellow
    Write-Host "  1. 检查 GitHub Actions 是否正在构建 Docker 镜像"
    Write-Host "  2. 在 Docker Hub 确认镜像发布成功"
    Write-Host "  3. 在 GitHub 创建 Release（如果 gh CLI 未安装）"
    Write-Host ""
}

# ============================================
# 主流程
# ============================================

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  Personal AI OS 发布脚本" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

# 确定版本号
$currentVersion = Get-CurrentVersion
Write-Host ""
Write-Host "当前版本: $currentVersion" -ForegroundColor Gray

if ($Version -eq "patch" -or $Version -eq "minor" -or $Version -eq "major") {
    # 自动递增版本
    $parts = $currentVersion.Split('.')
    switch ($Version) {
        "patch" { $parts[2] = [int]$parts[2] + 1 }
        "minor" { $parts[1] = [int]$parts[1] + 1; $parts[2] = 0 }
        "major" { $parts[0] = [int]$parts[0] + 1; $parts[1] = 0; $parts[2] = 0 }
    }
    $newVersion = $parts -join '.'
} elseif ($Version -match "^\d+\.\d+\.\d+$") {
    $newVersion = $Version
} else {
    Write-Host ""
    Write-Host "用法:" -ForegroundColor Yellow
    Write-Host "  .\scripts\release.ps1 1.1.0    # 指定版本号"
    Write-Host "  .\scripts\release.ps1 patch     # 递增补丁版本"
    Write-Host "  .\scripts\release.ps1 minor     # 递增次版本"
    Write-Host "  .\scripts\release.ps1 major     # 递增主版本"
    exit 1
}

Write-Host "新版本: $newVersion" -ForegroundColor Green

# 确认发布
$confirm = Read-Host "确认发布 v$newVersion? (y/n)"
if ($confirm -ne "y") {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

# 执行发布流程
Update-Version $newVersion

if (-not (Test-Build)) {
    Write-Error "测试未通过，取消发布"
    exit 1
}

if (-not (Build-Frontend)) {
    Write-Error "前端构建失败，取消发布"
    exit 1
}

Create-Commit $newVersion
Create-Tag $newVersion
Push-Changes $newVersion
Create-GitHubRelease $newVersion
Show-Summary $newVersion
