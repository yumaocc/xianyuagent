import time
import os
import re
import sys
import urllib3
import random

import requests
from loguru import logger
from utils.xianyu_utils import generate_sign
from user_agent_pool import get_ua_pool

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class XianyuApis:
    def __init__(self):
        self.url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/'
        self.session = requests.Session()
        
        # 禁用代理和配置SSL
        self.session.proxies = {}
        self.session.trust_env = False
        self.session.verify = False

        # 使用全局 User-Agent 池
        self.ua_pool = get_ua_pool()
        selected_ua = self.ua_pool.get_current_http_ua()
        
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'cache-control': 'no-cache',
            'origin': 'https://www.goofish.com',
            'pragma': 'no-cache',
            'referer': 'https://www.goofish.com/pc/message',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': selected_ua,
            'x-requested-with': 'XMLHttpRequest',
        })
        
    def clear_duplicate_cookies(self):
        """清理重复的cookies"""
        # 创建一个新的CookieJar
        new_jar = requests.cookies.RequestsCookieJar()
        
        # 记录已经添加过的cookie名称
        added_cookies = set()
        
        # 按照cookies列表的逆序遍历（最新的通常在后面）
        cookie_list = list(self.session.cookies)
        cookie_list.reverse()
        
        for cookie in cookie_list:
            # 如果这个cookie名称还没有添加过，就添加到新jar中
            if cookie.name not in added_cookies:
                new_jar.set_cookie(cookie)
                added_cookies.add(cookie.name)
                
        # 替换session的cookies
        self.session.cookies = new_jar
        
        # 更新完cookies后，更新.env文件
        self.update_env_cookies()
        
    def update_env_cookies(self):
        """更新.env文件中的COOKIES_STR"""
        try:
            # 获取当前cookies的字符串形式
            cookie_str = '; '.join([f"{cookie.name}={cookie.value}" for cookie in self.session.cookies])
            
            # 读取.env文件
            env_path = os.path.join(os.getcwd(), '.env')
            if not os.path.exists(env_path):
                logger.warning(".env文件不存在，无法更新COOKIES_STR")
                return
                
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.read()
                
            # 使用正则表达式替换COOKIES_STR的值
            if 'COOKIES_STR=' in env_content:
                new_env_content = re.sub(
                    r'COOKIES_STR=.*', 
                    f'COOKIES_STR={cookie_str}',
                    env_content
                )
                
                # 写回.env文件
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(new_env_content)
                    
                logger.debug("已更新.env文件中的COOKIES_STR")
            else:
                logger.warning(".env文件中未找到COOKIES_STR配置项")
        except Exception as e:
            logger.warning(f"更新.env文件失败: {str(e)}")
    
    def get_smart_delay(self, retry_count, base_delay=2, is_protection_error=False):
        """智能延时策略"""
        if is_protection_error:
            # 防护机制触发时使用指数退避
            delay = base_delay * (2 ** retry_count) + random.uniform(0, 5)
            return min(delay, 60)  # 最大60秒
        else:
            # 普通错误使用线性增长
            return base_delay + retry_count * 2 + random.uniform(0, 3)
        
    def hasLogin(self, retry_count=0):
        """调用hasLogin.do接口进行登录状态检查"""
        if retry_count >= 2:
            logger.error("Login检查失败，重试次数过多")
            return False
            
        try:
            url = 'https://passport.goofish.com/newlogin/hasLogin.do'
            params = {
                'appName': 'xianyu',
                'fromSite': '77'
            }
            data = {
                'hid': self.session.cookies.get('unb', ''),
                'ltl': 'true',
                'appName': 'xianyu',
                'appEntrance': 'web',
                '_csrf_token': self.session.cookies.get('XSRF-TOKEN', ''),
                'umidToken': '',
                'hsiz': self.session.cookies.get('cookie2', ''),
                'bizParams': 'taobaoBizLoginFrom=web',
                'mainPage': 'false',
                'isMobile': 'false',
                'lang': 'zh_CN',
                'returnUrl': '',
                'fromSite': '77',
                'isIframe': 'true',
                'documentReferer': 'https://www.goofish.com/',
                'defaultView': 'hasLogin',
                'umidTag': 'SERVER',
                'deviceId': self.session.cookies.get('cna', '')
            }
            
            response = self.session.post(url, params=params, data=data)
            res_json = response.json()
            
            if res_json.get('content', {}).get('success'):
                logger.debug("Login成功")
                # 清理和更新cookies
                self.clear_duplicate_cookies()
                return True
            else:
                logger.warning(f"Login失败: {res_json}")
                delay = random.uniform(2, 5) + retry_count * 2  # 递增延时
                logger.debug(f"等待 {delay:.1f} 秒后重试...")
                time.sleep(delay)
                return self.hasLogin(retry_count + 1)
                
        except Exception as e:
            logger.error(f"Login请求异常: {str(e)}")
            delay = random.uniform(3, 6) + retry_count * 2
            logger.debug(f"请求异常，等待 {delay:.1f} 秒后重试...")
            time.sleep(delay)
            return self.hasLogin(retry_count + 1)

    def get_token(self, device_id, retry_count=0):
        if retry_count >= 2:  # 最多重试3次
            logger.warning("获取token失败，尝试重新登陆")
            # 尝试通过hasLogin重新登录
            if self.hasLogin():
                logger.info("重新登录成功，重新尝试获取token")
                return self.get_token(device_id, 0)  # 重置重试次数
            else:
                logger.error("重新登录失败，Cookie已失效")
                logger.error("🔴 程序即将退出，请更新.env文件中的COOKIES_STR后重新启动")
                sys.exit(1)  # 直接退出程序
            
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
            'api': 'mtop.taobao.idlemessage.pc.login.token',
            'sessionOption': 'AutoLoginOnly',
            'spm_cnt': 'a21ybx.im.0.0',
        }
        data_val = '{"appKey":"444e9908a51d1cb236a27862abc769c9","deviceId":"' + device_id + '"}'
        data = {
            'data': data_val,
        }
        
        # 简单获取token，信任cookies已清理干净
        token = self.session.cookies.get('_m_h5_tk', '').split('_')[0]
        
        sign = generate_sign(params['t'], token, data_val)
        params['sign'] = sign
        
        try:
            response = self.session.post('https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/', params=params, data=data)
            res_json = response.json()
            
            if isinstance(res_json, dict):
                ret_value = res_json.get('ret', [])
                # 检查ret是否包含成功信息
                if not any('SUCCESS::调用成功' in ret for ret in ret_value):
                    # 检查是否是防护机制错误
                    if any('RGV587_ERROR::SM' in str(ret) for ret in ret_value):
                        delay = random.uniform(5, 15) + retry_count * 5  # 防护机制延时更长
                        logger.warning(f"触发防护机制，等待 {delay:.1f} 秒后重试...")
                    else:
                        delay = random.uniform(2, 4) + retry_count * 2
                        logger.warning(f"Token API调用失败，错误信息: {ret_value}")
                    
                    # 处理响应中的Set-Cookie
                    if 'Set-Cookie' in response.headers:
                        logger.debug("检测到Set-Cookie，更新cookie")
                        self.clear_duplicate_cookies()
                    
                    time.sleep(delay)
                    return self.get_token(device_id, retry_count + 1)
                else:
                    logger.info("Token获取成功")
                    return res_json
            else:
                logger.error(f"Token API返回格式异常: {res_json}")
                return self.get_token(device_id, retry_count + 1)
                
        except Exception as e:
            logger.error(f"Token API请求异常: {str(e)}")
            time.sleep(0.5)
            return self.get_token(device_id, retry_count + 1)

    def get_item_info(self, item_id, retry_count=0):
        """获取商品信息，自动处理token失效的情况"""
        if retry_count >= 3:  # 最多重试3次
            logger.error("获取商品信息失败，重试次数过多")
            return {"error": "获取商品信息失败，重试次数过多"}
            
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
            'api': 'mtop.taobao.idle.pc.detail',
            'sessionOption': 'AutoLoginOnly',
            'spm_cnt': 'a21ybx.im.0.0',
        }
        
        data_val = '{"itemId":"' + item_id + '"}'
        data = {
            'data': data_val,
        }
        
        # 简单获取token，信任cookies已清理干净
        token = self.session.cookies.get('_m_h5_tk', '').split('_')[0]
        
        sign = generate_sign(params['t'], token, data_val)
        params['sign'] = sign
        
        try:
            response = self.session.post(
                'https://h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail/1.0/', 
                params=params, 
                data=data
            )
            
            res_json = response.json()
            # 检查返回状态
            if isinstance(res_json, dict):
                ret_value = res_json.get('ret', [])
                # 检查ret是否包含成功信息
                if not any('SUCCESS::调用成功' in ret for ret in ret_value):
                    logger.warning(f"商品信息API调用失败，错误信息: {ret_value}")
                    # 处理响应中的Set-Cookie
                    if 'Set-Cookie' in response.headers:
                        logger.debug("检测到Set-Cookie，更新cookie")
                        self.clear_duplicate_cookies()
                    time.sleep(0.5)
                    return self.get_item_info(item_id, retry_count + 1)
                else:
                    logger.debug(f"商品信息获取成功: {item_id}")
                    return res_json
            else:
                logger.error(f"商品信息API返回格式异常: {res_json}")
                return self.get_item_info(item_id, retry_count + 1)
                
        except Exception as e:
            logger.error(f"商品信息API请求异常: {str(e)}")
            time.sleep(0.5)
            return self.get_item_info(item_id, retry_count + 1)

    def get_user_items(self, page=1, page_size=20, status='ALL', retry_count=0):
        """获取用户发布的商品列表

        Args:
            page: 页码，从1开始
            page_size: 每页数量
            status: 商品状态 ALL/ON_SALE/SOLD_OUT（注意：新API可能不支持此参数）
            retry_count: 重试次数

        Returns:
            dict: 包含商品列表的响应数据
        """
        if retry_count >= 3:
            logger.error("获取用户商品列表失败，重试次数过多")
            return {"error": "获取用户商品列表失败，重试次数过多"}

        # 获取userId
        user_id = None
        for cookie in self.session.cookies:
            if cookie.name == 'unb':
                user_id = cookie.value
                break

        if not user_id:
            logger.error("无法获取userId，请检查Cookie配置")
            return {"error": "无法获取userId"}

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
            'api': 'mtop.idle.web.xyh.item.list',
            'sessionOption': 'AutoLoginOnly',
        }

        # 构建请求数据 - 使用新API要求的参数格式
        data_val = f'{{"needGroupInfo":true,"pageNumber":{page},"userId":"{user_id}","pageSize":{page_size}}}'
        data = {
            'data': data_val,
        }

        # 获取token并生成签名（处理重复cookie）
        token = ''
        for cookie in self.session.cookies:
            if cookie.name == '_m_h5_tk':
                token = cookie.value.split('_')[0]
                break

        sign = generate_sign(params['t'], token, data_val)
        params['sign'] = sign

        try:
            response = self.session.post(
                'https://h5api.m.goofish.com/h5/mtop.idle.web.xyh.item.list/1.0/',
                params=params,
                data=data
            )

            res_json = response.json()

            # 检查返回状态
            if isinstance(res_json, dict):
                ret_value = res_json.get('ret', [])
                # 检查ret是否包含成功信息
                if not any('SUCCESS' in ret for ret in ret_value):
                    logger.warning(f"用户商品列表API调用失败，错误信息: {ret_value}")

                    # 处理响应中的Set-Cookie
                    if 'Set-Cookie' in response.headers:
                        logger.debug("检测到Set-Cookie，更新cookie")
                        self.clear_duplicate_cookies()

                    time.sleep(random.uniform(1, 3))
                    return self.get_user_items(page, page_size, status, retry_count + 1)
                else:
                    logger.debug(f"用户商品列表获取成功，页码: {page}")
                    return res_json
            else:
                logger.error(f"用户商品列表API返回格式异常: {res_json}")
                return self.get_user_items(page, page_size, status, retry_count + 1)

        except Exception as e:
            logger.error(f"用户商品列表API请求异常: {str(e)}")
            time.sleep(random.uniform(1, 2))
            return self.get_user_items(page, page_size, status, retry_count + 1)
