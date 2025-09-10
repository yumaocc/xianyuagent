#!/bin/bash

# SSL证书配置脚本 - 使用Let's Encrypt免费证书

set -e

echo "🔒 SSL证书配置脚本"
echo ""

# 获取域名信息
read -p "请输入您的域名 (例如: example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo "❌ 域名不能为空"
    exit 1
fi

read -p "请输入您的邮箱 (用于Let's Encrypt通知): " EMAIL
if [ -z "$EMAIL" ]; then
    echo "❌ 邮箱不能为空"  
    exit 1
fi

PROJECT_DIR="$HOME/apps/xianyu-agent"
SSL_DIR="$PROJECT_DIR/ssl"

echo "🔧 配置域名: $DOMAIN"
echo "📧 通知邮箱: $EMAIL"
echo ""

# 安装Certbot
echo "📦 安装Certbot..."
sudo apt update
sudo apt install -y snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

# 临时停止服务以释放80端口
echo "⏸️  临时停止服务..."
cd $PROJECT_DIR
docker-compose down 2>/dev/null || true

# 获取SSL证书
echo "🔒 获取SSL证书..."
sudo certbot certonly --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# 复制证书到项目目录
echo "📋 复制证书..."
mkdir -p $SSL_DIR
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/cert.pem
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/key.pem
sudo chown -R $USER:$USER $SSL_DIR

# 更新Nginx配置
echo "⚙️  更新Nginx配置..."
cat > $PROJECT_DIR/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream xianyu_web {
        server xianyu-web:5000;
    }
    
    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name $DOMAIN;
        return 301 https://\$server_name\$request_uri;
    }
    
    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name $DOMAIN;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        # SSL优化配置
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;
        
        # 现代SSL配置
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=63072000" always;
        
        # 反向代理配置
        location / {
            proxy_pass http://xianyu_web;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # WebSocket支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
EOF

# 启动完整版服务 (包含Nginx)
echo "🚀 启动HTTPS服务..."
docker-compose up -d

# 设置证书自动续期
echo "🔄 设置证书自动续期..."
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# 等待服务启动
sleep 10

echo ""
echo "✅ SSL证书配置完成！"
echo "🌐 HTTPS访问地址: https://$DOMAIN"
echo "🔒 证书有效期: 90天 (自动续期)"
echo ""
echo "📝 证书管理命令："
echo "   查看证书状态: sudo certbot certificates"
echo "   手动续期: sudo certbot renew"
echo "   测试续期: sudo certbot renew --dry-run"