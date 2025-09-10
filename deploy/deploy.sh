#!/bin/bash

# 闲鱼自动代理项目部署脚本
# 运行前请确保已执行 aliyun-setup.sh

set -e

PROJECT_DIR="~/apps/xianyu-agent"
REPO_URL="https://github.com/your-username/XianyuAutoAgent.git"  # 替换为您的仓库地址

echo "🚀 开始部署闲鱼自动代理项目..."

# 进入项目目录
cd $PROJECT_DIR

# 克隆或更新代码
if [ -d ".git" ]; then
    echo "📥 更新代码..."
    git pull origin main
else
    echo "📥 克隆代码..."
    git clone $REPO_URL .
fi

# 检查必要文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 创建环境配置文件..."
        cp .env.example .env
        echo "⚠️  请编辑 .env 文件配置您的参数："
        echo "   - API_KEY: 通义千问API密钥"
        echo "   - COOKIES_STR: 闲鱼登录Cookie"
        echo "   - 其他必要配置"
        echo ""
        echo "🔧 使用命令编辑: nano .env"
        read -p "按回车键继续 (请确保已配置.env文件)..."
    else
        echo "❌ 缺少环境配置文件，请创建 .env 文件"
        exit 1
    fi
fi

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p data prompts ssl logs

# 构建Docker镜像
echo "🐳 构建Docker镜像..."
docker-compose -f docker-compose.simple.yml build --no-cache

# 停止旧服务
echo "🛑 停止旧服务..."
docker-compose -f docker-compose.simple.yml down 2>/dev/null || true

# 启动服务
echo "🚀 启动服务..."
docker-compose -f docker-compose.simple.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.simple.yml ps

# 显示服务信息
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "获取失败")
echo ""
echo "✅ 部署完成！"
echo "🌐 服务访问地址："
echo "   Web管理界面: http://$PUBLIC_IP:5000"
echo "   如使用Nginx: http://$PUBLIC_IP"
echo ""
echo "📊 服务管理命令："
echo "   查看日志: docker-compose -f docker-compose.simple.yml logs -f"
echo "   重启服务: docker-compose -f docker-compose.simple.yml restart"
echo "   停止服务: docker-compose -f docker-compose.simple.yml down"
echo ""
echo "📝 后续操作："
echo "   1. 访问Web界面进行配置"
echo "   2. 上传闲鱼Cookie"
echo "   3. 测试消息回复功能"