#!/bin/bash

# 系统维护脚本

PROJECT_DIR="$HOME/apps/xianyu-agent"

show_help() {
    echo "🔧 闲鱼自动代理维护工具"
    echo ""
    echo "使用方法: $0 [操作]"
    echo ""
    echo "可用操作:"
    echo "  backup     - 备份数据"
    echo "  clean      - 清理日志和缓存"
    echo "  update     - 更新代码和服务"
    echo "  restart    - 重启所有服务"
    echo "  monitor    - 查看系统状态"
    echo "  logs       - 查看服务日志"
    echo "  help       - 显示此帮助信息"
}

backup_data() {
    echo "💾 开始数据备份..."
    
    BACKUP_DIR="$HOME/backups/xianyu-$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # 备份数据文件
    if [ -d "$PROJECT_DIR/data" ]; then
        cp -r $PROJECT_DIR/data $BACKUP_DIR/
        echo "   ✅ 数据文件已备份"
    fi
    
    # 备份配置文件
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp $PROJECT_DIR/.env $BACKUP_DIR/
        echo "   ✅ 配置文件已备份"
    fi
    
    # 备份提示词
    if [ -d "$PROJECT_DIR/prompts" ]; then
        cp -r $PROJECT_DIR/prompts $BACKUP_DIR/
        echo "   ✅ 提示词文件已备份"
    fi
    
    echo "   📁 备份位置: $BACKUP_DIR"
}

clean_system() {
    echo "🧹 开始系统清理..."
    
    cd $PROJECT_DIR
    
    # 清理Docker日志
    echo "   🐳 清理Docker日志..."
    docker system prune -f
    
    # 清理应用日志 (保留最近7天)
    if [ -d "logs" ]; then
        find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
        echo "   📝 已清理7天前的日志文件"
    fi
    
    # 清理临时文件
    find $PROJECT_DIR -name "*.tmp" -delete 2>/dev/null || true
    find $PROJECT_DIR -name ".DS_Store" -delete 2>/dev/null || true
    
    echo "   ✅ 清理完成"
}

update_service() {
    echo "🔄 开始更新服务..."
    
    cd $PROJECT_DIR
    
    # 备份当前数据
    echo "   💾 备份当前数据..."
    backup_data
    
    # 更新代码
    echo "   📥 更新代码..."
    git pull origin main
    
    # 重新构建并启动
    echo "   🏗️  重新构建镜像..."
    docker-compose -f docker-compose.simple.yml build --no-cache
    
    echo "   🚀 重启服务..."
    docker-compose -f docker-compose.simple.yml down
    docker-compose -f docker-compose.simple.yml up -d
    
    echo "   ✅ 更新完成"
}

restart_service() {
    echo "🔄 重启所有服务..."
    
    cd $PROJECT_DIR
    docker-compose -f docker-compose.simple.yml restart
    
    echo "   ⏳ 等待服务启动..."
    sleep 10
    
    echo "   🔍 检查服务状态..."
    docker-compose -f docker-compose.simple.yml ps
}

show_logs() {
    echo "📝 服务日志:"
    echo ""
    
    cd $PROJECT_DIR
    
    echo "=== Web服务日志 (最近20行) ==="
    docker-compose -f docker-compose.simple.yml logs --tail=20 xianyu-web
    
    echo ""
    echo "=== Agent服务日志 (最近20行) ==="
    docker-compose -f docker-compose.simple.yml logs --tail=20 xianyu-agent
}

# 主程序
case "${1:-help}" in
    backup)
        backup_data
        ;;
    clean)
        clean_system
        ;;
    update)
        update_service
        ;;
    restart)
        restart_service
        ;;
    monitor)
        bash $PROJECT_DIR/../monitor.sh
        ;;
    logs)
        show_logs
        ;;
    help|*)
        show_help
        ;;
esac