#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动XianyuAutoAgent Web API服务
"""

import sys
import os
import time
from loguru import logger
from web_admin_api import WebAdminAPI
from dotenv import load_dotenv


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

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
        api = WebAdminAPI()

        # 检查是否需要自动启动Agent
        auto_start = os.getenv("AUTO_START_AGENT", "false").lower() == "true"
        if auto_start:
            logger.info("🤖 检测到 AUTO_START_AGENT=true，将自动启动 AI Agent")
            # 等待API服务初始化
            time.sleep(1)
            # 自动启动Agent
            try:
                result = api._auto_start_agent()
                if result:
                    logger.info("✅ AI Agent 已自动启动")
                else:
                    logger.warning("⚠️  AI Agent 自动启动失败，请检查配置")
            except Exception as e:
                logger.error(f"❌ AI Agent 自动启动异常: {e}")

        # 启动服务（开发模式使用 Flask 内置服务器）
        logger.info("🚀 Web服务启动中...")
        logger.info("📱 管理界面地址: http://localhost:5000")
        logger.info("📊 API文档地址: http://localhost:5000/api")
        logger.info("⏹️  按 Ctrl+C 停止服务")
        logger.info("")
        logger.info("💡 开发模式运行中（支持热重载）")

        # 判断运行模式
        run_mode = os.getenv("RUN_MODE", "dev")

        if run_mode == "production":
            # 生产模式：使用 gunicorn
            try:
                import subprocess
                subprocess.run([
                    'gunicorn',
                    '--bind', '0.0.0.0:5000',
                    '--workers', '2',
                    '--timeout', '120',
                    '--access-logfile', '-',
                    '--error-logfile', '-',
                    'web_api:create_app()'
                ])
            except FileNotFoundError:
                logger.error("❌ gunicorn 未安装，请运行: pip install gunicorn")
                logger.info("💡 或将 .env 中的 RUN_MODE 设置为 dev")
                sys.exit(1)
        else:
            # 开发模式：使用 Flask 内置服务器
            api.app.run(
                host='0.0.0.0',
                port=5000,
                debug=True,
                use_reloader=True,
                threaded=True
            )

    except KeyboardInterrupt:
        logger.info("👋 Web服务已停止")
    except Exception as e:
        logger.error(f"❌ Web服务启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()