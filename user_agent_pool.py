"""
User-Agent 池管理器
用于提供随机 User-Agent，减少风控概率
"""
import random


class UserAgentPool:
    """User-Agent 池"""

    def __init__(self):
        self.user_agents = [
            # Chrome - Windows (最新版本)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',

            # Chrome - macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',

            # Safari - macOS (最常见的真实浏览器)
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',

            # Edge - Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
            'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',

            # Firefox - Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',

            # Firefox - macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:123.0) Gecko/20100101 Firefox/123.0',
        ]

        # WebSocket 专用 User-Agent (带 DingTalk 标识)
        self.websocket_user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Windows/10) Browser(Chrome/131.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Windows/10) Browser(Chrome/132.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Windows/10) Browser(Chrome/133.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5',
            'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Windows/11) Browser(Chrome/131.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5',
            'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Windows/11) Browser(Chrome/132.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Mac/10.15.7) Browser(Chrome/131.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Mac/10.15.7) Browser(Chrome/132.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Mac/14.1) Browser(Chrome/131.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5',
        ]

        # 当前选择的 User-Agent
        self.current_http_ua = None
        self.current_websocket_ua = None

    def get_random_http_ua(self):
        """获取随机 HTTP User-Agent"""
        self.current_http_ua = random.choice(self.user_agents)
        return self.current_http_ua

    def get_random_websocket_ua(self):
        """获取随机 WebSocket User-Agent (带 DingTalk 标识)"""
        self.current_websocket_ua = random.choice(self.websocket_user_agents)
        return self.current_websocket_ua

    def get_current_http_ua(self):
        """获取当前 HTTP User-Agent"""
        if not self.current_http_ua:
            self.current_http_ua = self.get_random_http_ua()
        return self.current_http_ua

    def get_current_websocket_ua(self):
        """获取当前 WebSocket User-Agent"""
        if not self.current_websocket_ua:
            self.current_websocket_ua = self.get_random_websocket_ua()
        return self.current_websocket_ua

    def rotate(self):
        """轮换 User-Agent"""
        self.current_http_ua = self.get_random_http_ua()
        self.current_websocket_ua = self.get_random_websocket_ua()
        return self.current_http_ua, self.current_websocket_ua


# 全局单例
_ua_pool = UserAgentPool()


def get_ua_pool():
    """获取全局 User-Agent 池"""
    return _ua_pool
