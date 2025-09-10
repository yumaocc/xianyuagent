#!/bin/bash

# 闲鱼自动代理 + Web管理端 多项目部署脚本

set -e

echo "🎉 闲鱼自动代理多项目部署脚本"
echo "📦 将部署以下项目："
echo "   • XianyuAutoAgent (后端API + AI服务)"
echo "   • xianyu-admin-web (前端管理界面)"
echo ""

# 获取项目信息
read -p "后端项目GitHub地址: " BACKEND_REPO
if [ -z "$BACKEND_REPO" ]; then
    BACKEND_REPO="https://github.com/your-username/XianyuAutoAgent.git"
fi

read -p "前端项目GitHub地址: " FRONTEND_REPO
if [ -z "$FRONTEND_REPO" ]; then
    FRONTEND_REPO="https://github.com/your-username/xianyu-admin-web.git"
fi

read -p "通义千问API密钥: " API_KEY
read -p "闲鱼Cookie (可选): " COOKIES_STR

PROJECT_DIR="$HOME/apps/xianyu-full-stack"

echo ""
echo "🚀 开始多项目部署..."

# 第一步：环境准备
echo "📦 1. 准备系统环境..."
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

# 安装Node.js (前端构建需要)
if ! command -v node &> /dev/null; then
    echo "📦 安装Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# 第二步：创建项目目录结构
echo "📁 2. 创建项目目录..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 下载后端项目
echo "📥 3. 下载后端项目..."
if [ -d "backend" ]; then
    cd backend && git pull origin main && cd ..
else
    git clone $BACKEND_REPO backend
fi

# 下载前端项目
echo "📥 4. 下载前端项目..."
if [ -d "frontend" ]; then
    cd frontend && git pull origin main && cd ..
else
    git clone $FRONTEND_REPO frontend
fi

# 第三步：配置后端环境
echo "⚙️  5. 配置后端环境..."
cd backend
if [ ! -f ".env" ]; then
    cp .env.example .env
    
    if [ ! -z "$API_KEY" ]; then
        sed -i "s/API_KEY=.*/API_KEY=$API_KEY/" .env
    fi
    
    if [ ! -z "$COOKIES_STR" ]; then
        sed -i "s/COOKIES_STR=.*/COOKIES_STR=$COOKIES_STR/" .env
    fi
fi

# 创建后端数据目录
mkdir -p data prompts ssl logs
cd ..

# 第四步：构建前端
echo "🏗️  6. 构建前端项目..."
cd frontend
npm install
npm run build
cd ..

# 第五步：创建统一的Docker配置
echo "🐳 7. 创建Docker配置..."

# 创建多项目Docker Compose文件
cat > docker-compose.full.yml << 'EOF'
version: '3.8'

services:
  # 后端API服务
  xianyu-api:
    build: ./backend
    container_name: xianyu-api
    restart: unless-stopped
    volumes:
      - ./backend/data:/app/data
      - ./backend/prompts:/app/prompts
      - ./backend/.env:/app/.env
    environment:
      - TZ=Asia/Shanghai
      - PYTHONUNBUFFERED=1
      - FLASK_ENV=production
    networks:
      - xianyu-network
    ports:
      - "5000:5000"
    command: ["python", "web_api.py"]

  # 后端AI客服服务
  xianyu-agent:
    build: ./backend
    container_name: xianyu-agent
    restart: unless-stopped
    volumes:
      - ./backend/data:/app/data
      - ./backend/prompts:/app/prompts
      - ./backend/.env:/app/.env
    environment:
      - TZ=Asia/Shanghai
      - PYTHONUNBUFFERED=1
    networks:
      - xianyu-network
    depends_on:
      - xianyu-api
    command: ["python", "main.py"]

  # 前端Web界面
  xianyu-web:
    image: nginx:alpine
    container_name: xianyu-web
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx-full.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - xianyu-network
    depends_on:
      - xianyu-api

networks:
  xianyu-network:
    driver: bridge
EOF

# 创建Nginx配置文件
cat > nginx-full.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # 后端API服务
    upstream api_backend {
        server xianyu-api:5000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
            
            # 缓存静态资源
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
        
        # API代理
        location /api/ {
            proxy_pass http://api_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # 解决跨域
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS, PUT, DELETE';
            add_header Access-Control-Allow-Headers 'DNT,X-Mx-ReqToken,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization';
            
            if ($request_method = 'OPTIONS') {
                return 204;
            }
        }
    }
}
EOF

# 配置防火墙
echo "🛡️ 8. 配置防火墙..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5000/tcp
echo "y" | sudo ufw enable

# 第六步：启动所有服务
echo "🚀 9. 启动所有服务..."
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 20

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.full.yml ps

# 获取公网IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "获取失败")

echo ""
echo "🎉 多项目部署完成！"
echo "=========================================="
echo "🌐 前端管理界面: http://$PUBLIC_IP"
echo "🔌 后端API接口: http://$PUBLIC_IP/api"
echo "📊 API文档: http://$PUBLIC_IP:5000/docs"
echo "📁 项目目录: $PROJECT_DIR"
echo "=========================================="
echo ""
echo "📝 服务说明："
echo "   • 前端界面 (端口80): React管理界面"
echo "   • 后端API (端口5000): RESTful接口"
echo "   • AI客服服务: 自动回复闲鱼消息"
echo ""
echo "🔧 管理命令："
echo "   查看日志: docker-compose -f docker-compose.full.yml logs -f"
echo "   重启服务: docker-compose -f docker-compose.full.yml restart"
echo "   停止服务: docker-compose -f docker-compose.full.yml down"
echo "   更新项目: ./update-projects.sh"

# 创建更新脚本
cat > update-projects.sh << 'EOF'
#!/bin/bash
echo "🔄 更新所有项目..."

# 更新后端
cd backend
git pull origin main
cd ..

# 更新前端并重新构建
cd frontend  
git pull origin main
npm install
npm run build
cd ..

# 重启服务
docker-compose -f docker-compose.full.yml up -d --build

echo "✅ 项目更新完成！"
EOF

chmod +x update-projects.sh

echo ""
if [ -z "$API_KEY" ] || [ -z "$COOKIES_STR" ]; then
    echo "⚠️  重要提醒："
    echo "   请编辑配置文件: nano backend/.env"
    echo "   配置完成后重启: docker-compose -f docker-compose.full.yml restart"
fi

echo ""
echo "🎯 接下来的步骤："
echo "   1. 访问 http://$PUBLIC_IP 打开管理界面"
echo "   2. 在界面中完成剩余配置"
echo "   3. 测试功能是否正常"