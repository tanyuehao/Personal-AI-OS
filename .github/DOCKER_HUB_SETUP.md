# Docker Hub 配置指南

## 1. 创建 Docker Hub 账号

1. 访问 https://hub.docker.com/
2. 注册账号并登录

## 2. 创建 Access Token

1. 登录 Docker Hub
2. 点击右上角头像 → Account Settings → Security
3. 点击 "New Access Token"
4. 给 Token 一个描述（如 `github-actions`）
5. 选择权限：Read & Write
6. 复制生成的 Token

## 3. 在 GitHub 仓库添加 Secrets

1. 打开 https://github.com/tanyuehao/Personal-AI-OS/settings/secrets/actions
2. 点击 "New repository secret"
3. 添加以下 Secrets：

| Name | Value |
|------|-------|
| `DOCKERHUB_USERNAME` | 你的 Docker Hub 用户名 |
| `DOCKERHUB_TOKEN` | 上面创建的 Access Token |

## 4. 触发自动发布

### 自动触发（推荐）

当你推送 Tag 时，会自动构建并发布 Docker 镜像：

```bash
git tag v1.0.0
git push origin v1.0.0
```

### 手动触发

1. 打开 https://github.com/tanyuehao/Personal-AI-OS/actions
2. 选择 "Build and Push Docker Images" workflow
3. 点击 "Run workflow"

## 5. 拉取镜像

发布成功后，用户可以这样拉取镜像：

```bash
# 拉取最新版本
docker pull tanyuehao/personal-ai-os-backend:1.0.0
docker pull tanyuehao/personal-ai-os-frontend:1.0.0

# 使用 docker-compose（更新 docker-compose.yml 中的 image 配置）
docker-compose pull
docker-compose up -d
```

## 6. 镜像命名规则

| 镜像 | 说明 |
|------|------|
| `tanyuehao/personal-ai-os-backend:v1.0.0` | 指定版本 |
| `tanyuehao/personal-ai-os-backend:1.0` | 主版本.次版本 |
| `tanyuehao/personal-ai-os-backend:sha-abc1234` | Git commit SHA |
| `tanyuehao/personal-ai-os-backend:latest` | 最新版本 |
