#!/bin/bash

# 闲鱼自动代理一键部署脚本 - 阿里云ECS专用
# 从零开始自动配置整个环境

set -e

echo "🎉 欢迎使用闲鱼自动代理一键部署脚本！"
echo "📋 此脚本将会："
echo "   1. 配置系统环境 (Docker, 工具等)"
echo "   2. 下载项目代码"
echo "   3. 配置服务"
echo "   4. 启动应用"
echo ""
read -p "确认开始部署吗？(y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "❌ 部署已取消"
    exit 1
fi

# 获取项目信息
echo ""
echo "📝 请提供以下信息："
read -p "GitHub仓库地址 (或直接回车使用示例): " REPO_URL
if [ -z "$REPO_URL" ]; then
    REPO_URL="https://github.com/shaxiu/XianyuAutoAgent.git"
fi

read -p "通义千问API密钥: " API_KEY
if [ -z "$API_KEY" ]; then
    echo "⚠️  API密钥为空，稍后需要手动配置"
fi

read -p "闲鱼Cookie (可选，稍后配置): " COOKIES_STR

PROJECT_DIR="$HOME/apps/xianyu-agent"

echo ""
echo "🚀 开始部署流程..."

# 第一步：配置系统环境
echo "📦 1. 配置系统环境..."
sudo apt update -y
sudo apt install -y curl wget git vim htop tree unzip

# 安装Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 安装Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 第二步：下载项目代码
echo "📥 2. 下载项目代码..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

if [ -d ".git" ]; then
    git pull origin main
else
    git clone $REPO_URL .
fi

# 第三步：配置环境
echo "⚙️  3. 配置环境..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    
    # 自动配置已提供的参数
    if [ ! -z "$API_KEY" ]; then
        sed -i "s/API_KEY=.*/API_KEY=$API_KEY/" .env
    fi
    
    if [ ! -z "$COOKIES_STR" ]; then
        sed -i "s/COOKIES_STR=.*/COOKIES_STR=$COOKIES_STR/" .env
    fi
fi

# 创建必要目录
mkdir -p data prompts ssl logs
sudo chown -R $USER:$USER $PROJECT_DIR

# 配置防火墙
echo "🛡️ 配置防火墙..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp  
sudo ufw allow 5000/tcp
echo "y" | sudo ufw enable

# 第四步：启动服务
echo "🚀 4. 启动服务..."
docker-compose -f docker-compose.simple.yml build
docker-compose -f docker-compose.simple.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.simple.yml ps

# 获取公网IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "获取失败")

echo ""
echo "🎉 部署完成！"
echo "===========================================" 
echo "🌐 访问地址: http://$PUBLIC_IP:5000"
echo "📁 项目目录: $PROJECT_DIR"
echo "🔧 配置文件: $PROJECT_DIR/.env"
echo "==========================================="
echo ""
echo "📝 接下来的步骤："
echo "   1. 访问 http://$PUBLIC_IP:5000 打开管理界面"
echo "   2. 如未配置，请编辑 .env 文件添加API密钥和Cookie"
echo "   3. 重启服务使配置生效: docker-compose restart"
echo "   4. 测试消息回复功能"
echo ""
echo "🔧 常用管理命令："
echo "   查看日志: cd $PROJECT_DIR && docker-compose -f docker-compose.simple.yml logs -f"
echo "   重启服务: cd $PROJECT_DIR && docker-compose -f docker-compose.simple.yml restart"
echo "   停止服务: cd $PROJECT_DIR && docker-compose -f docker-compose.simple.yml down"
echo "   更新代码: cd $PROJECT_DIR && git pull && docker-compose -f docker-compose.simple.yml up -d --build"
echo ""

if [ -z "$API_KEY" ] || [ -z "$COOKIES_STR" ]; then
    echo "⚠️  重要提醒："
    echo "   请编辑配置文件: nano $PROJECT_DIR/.env"
    echo "   配置完成后重启: cd $PROJECT_DIR && docker-compose -f docker-compose.simple.yml restart"
fi