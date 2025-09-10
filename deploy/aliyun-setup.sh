#!/bin/bash

# 阿里云ECS服务器环境配置脚本
# 适用于Ubuntu 22.04 LTS

set -e

echo "🚀 开始配置阿里云ECS环境..."

# 更新系统
echo "📦 更新系统包..."
sudo apt update && sudo apt upgrade -y

# 安装必要的系统工具
echo "🔧 安装系统工具..."
sudo apt install -y curl wget git vim htop tree unzip

# 安装Docker
echo "🐳 安装Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 添加当前用户到docker组
sudo usermod -aG docker $USER

# 安装Docker Compose
echo "📦 安装Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 创建项目目录
echo "📁 创建项目目录..."
mkdir -p ~/apps/xianyu-agent
cd ~/apps/xianyu-agent

# 配置防火墙
echo "🛡️ 配置防火墙..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5000/tcp
sudo ufw --force enable

# 设置时区
echo "⏰ 设置时区..."
sudo timedatectl set-timezone Asia/Shanghai

# 创建数据目录
echo "📂 创建数据目录..."
mkdir -p data prompts ssl

# 设置文件权限
sudo chown -R $USER:$USER ~/apps/xianyu-agent

echo "✅ 环境配置完成！"
echo "📝 请注意："
echo "   1. 重新登录SSH以使Docker组生效"
echo "   2. 运行 'docker --version' 验证安装"
echo "   3. 项目目录: ~/apps/xianyu-agent"

# 显示系统信息
echo "📊 系统信息："
echo "   CPU: $(nproc) 核心"
echo "   内存: $(free -h | awk '/^Mem:/ {print $2}')"
echo "   磁盘: $(df -h / | awk 'NR==2 {print $4}') 可用"
echo "   IP: $(curl -s ifconfig.me 2>/dev/null || echo '获取失败')"