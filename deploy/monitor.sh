#!/bin/bash

# 系统监控脚本

PROJECT_DIR="$HOME/apps/xianyu-agent"

echo "📊 闲鱼自动代理系统监控报告"
echo "=================================="
echo "⏰ 检查时间: $(date)"
echo ""

# 检查服务状态
echo "🔍 服务状态:"
cd $PROJECT_DIR
docker-compose -f docker-compose.simple.yml ps
echo ""

# 检查系统资源
echo "💻 系统资源:"
echo "   CPU使用率: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "   内存使用: $(free -h | awk '/^Mem:/ {printf "已用:%s/%s (%.1f%%)\n", $3,$2,$3/$2 * 100.0}')"
echo "   磁盘使用: $(df -h / | awk 'NR==2 {printf "已用:%s/%s (%s)\n", $3,$2,$5}')"
echo ""

# 检查网络连通性
echo "🌐 网络连通性:"
if ping -c 1 8.8.8.8 &> /dev/null; then
    echo "   ✅ 外网连接正常"
else
    echo "   ❌ 外网连接异常"
fi

# 检查端口状态
echo "🔌 端口状态:"
if netstat -tuln | grep -q ":5000 "; then
    echo "   ✅ 端口5000正常监听"
else
    echo "   ❌ 端口5000未监听"
fi

# 检查Docker容器日志 (最近50行)
echo ""
echo "📝 最近日志 (最后10行):"
echo "--- xianyu-web ---"
docker-compose -f docker-compose.simple.yml logs --tail=10 xianyu-web 2>/dev/null || echo "   获取日志失败"
echo ""
echo "--- xianyu-agent ---"
docker-compose -f docker-compose.simple.yml logs --tail=10 xianyu-agent 2>/dev/null || echo "   获取日志失败"

# 检查数据库文件
echo ""
echo "📂 数据文件状态:"
if [ -f "$PROJECT_DIR/data/chat_history.db" ]; then
    SIZE=$(du -h "$PROJECT_DIR/data/chat_history.db" | cut -f1)
    echo "   ✅ 聊天历史数据库: $SIZE"
else
    echo "   ⚠️  聊天历史数据库不存在"
fi

if [ -f "$PROJECT_DIR/data/chat_messages.json" ]; then
    SIZE=$(du -h "$PROJECT_DIR/data/chat_messages.json" | cut -f1)  
    echo "   ✅ 消息缓存文件: $SIZE"
else
    echo "   ⚠️  消息缓存文件不存在"
fi

# 检查配置文件
echo ""
echo "⚙️  配置文件检查:"
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "   ✅ 环境配置文件存在"
    if grep -q "API_KEY=.*[^=]$" "$PROJECT_DIR/.env"; then
        echo "   ✅ API密钥已配置"
    else
        echo "   ⚠️  API密钥未配置"
    fi
    if grep -q "COOKIES_STR=.*[^=]$" "$PROJECT_DIR/.env"; then
        echo "   ✅ Cookie已配置"
    else
        echo "   ⚠️  Cookie未配置"
    fi
else
    echo "   ❌ 环境配置文件不存在"
fi

echo ""
echo "=================================="
echo "💡 管理建议:"
echo "   • 定期清理日志文件避免磁盘空间不足"
echo "   • 监控内存使用情况，必要时重启服务"
echo "   • 备份重要数据文件到其他位置"
echo "   • 检查服务运行日志排查异常"