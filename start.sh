#!/bin/bash
# Personal AI OS 快速启动脚本

echo "🧠 Personal AI OS - 快速启动"
echo "=============================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 请先安装 docker-compose"
    exit 1
fi

# 检查 .env 文件
if [ ! -f backend/.env ]; then
    echo "📋 创建 .env 文件..."
    cp backend/.env.example backend/.env
    echo "⚠️  请编辑 backend/.env 配置你的 API 密钥"
    echo ""
    echo "推荐配置："
    echo "1. DeepSeek（便宜好用）: https://platform.deepseek.com/"
    echo "2. 小米 MiMo（免费额度）: https://siliconflow.cn/"
    echo ""
fi

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

echo ""
echo "✅ 服务已启动！"
echo ""
echo "访问地址："
echo "  - 前端: http://localhost:3000"
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/docs"
echo ""
echo "首次使用请："
echo "1. 编辑 backend/.env 配置 API 密钥"
echo "2. 重启服务: docker-compose restart backend"
echo ""
