#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试新的闲鱼API接口"""

import os
import sys
import time
import json
from dotenv import load_dotenv
from loguru import logger
from XianyuApis import XianyuApis
from utils.xianyu_utils import trans_cookies, generate_sign

logger.remove()
logger.add(sys.stdout, level="DEBUG")

def test_new_api():
    """测试新的API接口: mtop.idle.web.xyh.item.list"""
    load_dotenv()

    cookies_str = os.getenv("COOKIES_STR")
    if not cookies_str:
        logger.error("未配置COOKIES_STR")
        return

    api = XianyuApis()
    cookies = trans_cookies(cookies_str)
    api.session.cookies.update(cookies)

    # 先登录刷新token
    logger.info("登录并刷新token...")
    if not api.hasLogin():
        logger.error("登录失败")
        return

    # 获取device_id并刷新token
    device_id = None
    for cookie in api.session.cookies:
        if cookie.name == 'cna':
            device_id = cookie.value
            break

    if device_id:
        logger.info(f"获取token, device_id: {device_id}")
        token_result = api.get_token(device_id)
        logger.info(f"Token结果: {token_result}")

    # 测试新API
    api_name = 'mtop.idle.web.xyh.item.list'

    params = {
        'jsv': '2.7.2',
        'appKey': '34839810',
        't': str(int(time.time()) * 1000),
        'sign': '',
        'v': '1.0',
        'type': 'originaljson',
        'accountSite': 'xianyu',
        'dataType': 'json',
        'timeout': '20000',
        'api': api_name,
        'sessionOption': 'AutoLoginOnly',
    }

    # 获取userId
    user_id = None
    for cookie in api.session.cookies:
        if cookie.name == 'unb':
            user_id = cookie.value
            break

    logger.info(f"用户ID: {user_id}")

    # 尝试不同的data参数
    data_options = [
        f'{{"pageNumber":1,"pageSize":20,"userId":"{user_id}"}}',
        f'{{"pageNumber":1,"pageSize":20,"userId":{user_id}}}',
    ]

    for data_val in data_options:
        logger.info(f"\n测试data参数: {data_val}")
        data = {'data': data_val}

        # 获取token（处理重复cookie的情况）
        token = ''
        for cookie in api.session.cookies:
            if cookie.name == '_m_h5_tk':
                token = cookie.value.split('_')[0]
                break

        sign = generate_sign(params['t'], token, data_val)
        params['sign'] = sign

        try:
            url = f'https://h5api.m.goofish.com/h5/{api_name}/1.0/'
            response = api.session.post(url, params=params, data=data)
            res_json = response.json()

            logger.info(f"响应: {json.dumps(res_json, ensure_ascii=False, indent=2)}")

            if isinstance(res_json, dict):
                ret_value = res_json.get('ret', [])
                if any('SUCCESS' in ret for ret in ret_value):
                    logger.success(f"✅ 成功! data参数: {data_val}")

                    # 分析数据结构
                    if 'data' in res_json:
                        logger.info("=" * 60)
                        logger.info("数据结构分析:")
                        logger.info("=" * 60)
                        logger.info(json.dumps(res_json['data'], ensure_ascii=False, indent=2)[:2000])
                    return
                else:
                    logger.warning(f"失败: {ret_value}")
        except Exception as e:
            logger.error(f"异常: {e}")

        time.sleep(1)

if __name__ == '__main__':
    test_new_api()
