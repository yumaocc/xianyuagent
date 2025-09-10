#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动XianyuAutoAgent Web API服务
"""

import sys
import os
from loguru import logger
from web_api import XianyuWebAPI


def main():
    """主函数"""
    # 设置日志
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    logger.info("🌐 启动XianyuAutoAgent Web管理界面")
    logger.info("📂 确保.env文件已正确配置")
    
    try:
        # 创建并启动API服务
        api = XianyuWebAPI()
        
        # 启动服务
        logger.info("🚀 Web服务启动中...")
        logger.info("📱 管理界面地址: http://localhost:5000")
        logger.info("📊 API文档地址: http://localhost:5000/api")
        logger.info("⏹️  按 Ctrl+C 停止服务")
        
        api.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        logger.info("👋 Web服务已停止")
    except Exception as e:
        logger.error(f"❌ Web服务启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()