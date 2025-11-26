#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼API测试工具
用于测试不同的API接口，找到正确的商品列表接口
"""

import os
import sys
import time
import json
from dotenv import load_dotenv
from loguru import logger
from XianyuApis import XianyuApis
from utils.xianyu_utils import trans_cookies, generate_sign

# 配置日志
logger.remove()
logger.add(sys.stdout, level="DEBUG")

# 可能的API接口列表（根据闲鱼网站抓包获取）
POSSIBLE_APIS = [
    'mtop.taobao.idle.user.page.my.items',  # 原接口
    'mtop.taobao.idle.user.page.items',
    'mtop.taobao.idle.item.list.my',
    'mtop.taobao.idlemtopsearch.item.search.list',
    'mtop.idle.user.page.my.items',
    'mtop.taobao.idleitem.list',
    'mtop.taobao.idle.user.item.list',
]

def test_api_endpoint(api_instance, api_name):
    """测试单个API接口"""
    logger.info(f"\n{'='*60}")
    logger.info(f"测试API: {api_name}")
    logger.info(f"{'='*60}")

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

    data_val = '{"page":1,"pageSize":20,"status":"ALL"}'
    data = {'data': data_val}

    # 获取token并生成签名
    token = api_instance.session.cookies.get('_m_h5_tk', '').split('_')[0]
    sign = generate_sign(params['t'], token, data_val)
    params['sign'] = sign

    try:
        url = f'https://h5api.m.goofish.com/h5/{api_name}/1.0/'
        response = api_instance.session.post(url, params=params, data=data)
        res_json = response.json()

        logger.debug(f"响应状态码: {response.status_code}")
        logger.debug(f"响应数据: {json.dumps(res_json, ensure_ascii=False, indent=2)}")

        if isinstance(res_json, dict):
            ret_value = res_json.get('ret', [])

            # 检查是否成功
            if any('SUCCESS::调用成功' in ret for ret in ret_value):
                logger.success(f"✅ API调用成功: {api_name}")

                # 尝试解析数据
                if 'data' in res_json:
                    data_obj = res_json['data']
                    logger.info(f"数据结构: {json.dumps(data_obj, ensure_ascii=False, indent=2)[:500]}")

                    # 尝试找到商品列表
                    if isinstance(data_obj, dict):
                        for key in ['itemList', 'items', 'list', 'data']:
                            if key in data_obj:
                                logger.success(f"找到商品列表字段: {key}")
                                items = data_obj[key]
                                if isinstance(items, list) and len(items) > 0:
                                    logger.success(f"商品数量: {len(items)}")
                                    logger.info(f"第一个商品示例: {json.dumps(items[0], ensure_ascii=False, indent=2)[:300]}")
                                break

                return True
            else:
                error_msg = ', '.join(ret_value)
                logger.warning(f"❌ API调用失败: {error_msg}")
                return False
        else:
            logger.error(f"❌ API返回格式异常")
            return False

    except Exception as e:
        logger.error(f"❌ 请求异常: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("闲鱼API接口测试工具")
    logger.info("=" * 80)

    # 加载环境变量
    load_dotenv()

    # 检查Cookie配置
    cookies_str = os.getenv("COOKIES_STR")
    if not cookies_str:
        logger.error("错误: 未配置COOKIES_STR环境变量")
        logger.info("请在.env文件中配置COOKIES_STR")
        return

    # 初始化API
    logger.info("初始化闲鱼API...")
    api = XianyuApis()
    cookies = trans_cookies(cookies_str)
    api.session.cookies.update(cookies)

    # 测试登录状态
    logger.info("\n检查登录状态...")
    if api.hasLogin():
        logger.success("✅ 登录状态正常")
    else:
        logger.error("❌ 登录失败，请检查Cookie是否有效")
        return

    # 测试所有可能的API接口
    logger.info("\n开始测试所有可能的API接口...")
    successful_apis = []

    for api_name in POSSIBLE_APIS:
        if test_api_endpoint(api, api_name):
            successful_apis.append(api_name)
        time.sleep(2)  # 避免请求过快

    # 输出总结
    logger.info("\n" + "=" * 80)
    logger.info("测试结果总结")
    logger.info("=" * 80)

    if successful_apis:
        logger.success(f"找到 {len(successful_apis)} 个可用的API接口:")
        for api_name in successful_apis:
            logger.success(f"  ✅ {api_name}")

        logger.info("\n建议:")
        logger.info(f"请将 XianyuApis.py 第375行的API名称修改为:")
        logger.info(f"  'api': '{successful_apis[0]}'")
    else:
        logger.error("❌ 未找到可用的API接口")
        logger.info("\n可能的原因:")
        logger.info("1. Cookie已失效，请重新获取")
        logger.info("2. 闲鱼API接口已完全变更")
        logger.info("3. 需要通过浏览器开发者工具抓包查看实际使用的API")

        logger.info("\n如何获取正确的API接口:")
        logger.info("1. 打开浏览器，访问 https://www.goofish.com")
        logger.info("2. 登录并进入'我的发布'页面")
        logger.info("3. 打开开发者工具(F12) -> Network标签")
        logger.info("4. 刷新页面，查找包含商品列表数据的请求")
        logger.info("5. 查看请求URL中的'api'参数值")

if __name__ == '__main__':
    main()
