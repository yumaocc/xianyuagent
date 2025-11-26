#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取用户信息"""

import os
import sys
import json
from dotenv import load_dotenv
from loguru import logger
from XianyuApis import XianyuApis
from utils.xianyu_utils import trans_cookies

logger.remove()
logger.add(sys.stdout, level="DEBUG")

def get_user_info():
    """获取用户信息"""
    load_dotenv()

    cookies_str = os.getenv("COOKIES_STR")
    if not cookies_str:
        logger.error("未配置COOKIES_STR")
        return

    api = XianyuApis()
    cookies = trans_cookies(cookies_str)
    api.session.cookies.update(cookies)

    # 从Cookie中获取用户信息
    logger.info("从Cookie中获取的用户信息:")
    logger.info("=" * 60)

    user_info = {}
    for cookie in api.session.cookies:
        if cookie.name in ['unb', 'cookie2', '_tb_token_', 'cna', 'tracknick', 'uc1', 'uc3']:
            user_info[cookie.name] = cookie.value
            logger.info(f"{cookie.name}: {cookie.value}")

    logger.info("=" * 60)

    # 尝试解析unb（用户ID）
    if 'unb' in user_info:
        logger.success(f"用户ID (unb): {user_info['unb']}")

    if 'tracknick' in user_info:
        logger.success(f"用户昵称 (tracknick): {user_info['tracknick']}")

    return user_info

if __name__ == '__main__':
    get_user_info()
