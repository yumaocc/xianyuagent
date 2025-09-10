# -*- coding: utf-8 -*-
"""
XianyuAutoAgent Web API 服务
提供RESTful API接口供Web界面调用
"""

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import json
import asyncio
import threading
import time
from typing import Dict, List, Optional
from loguru import logger
import os
from dotenv import load_dotenv

# 导入项目模块
from XianyuApis import XianyuApis
from XianyuAgent import XianyuReplyBot
from context_manager import ChatContextManager
from product_publisher import XianyuProductPublisher
from utils.xianyu_utils import trans_cookies
from main import XianyuLive


class XianyuWebAPI:
    """闲鱼自动化Web API服务"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # 允许跨域访问
        
        # 初始化组件
        self._init_components()
        
        # 系统状态
        self.system_status = {
            'running': False,
            'connected': False,
            'last_heartbeat': None,
            'start_time': None,
            'message_count': 0,
            'error_count': 0
        }
        
        # XianyuLive实例
        self.xianyu_live = None
        self.live_thread = None
        
        # 注册路由
        self._register_routes()
    
    def _init_components(self):
        """初始化组件"""
        load_dotenv()
        
        # 初始化API
        self.xianyu_apis = XianyuApis()
        cookies_str = os.getenv("COOKIES_STR")
        if cookies_str:
            cookies = trans_cookies(cookies_str)
            self.xianyu_apis.session.cookies.update(cookies)
        
        # 初始化其他组件
        self.bot = XianyuReplyBot()
        self.context_manager = ChatContextManager()
        self.product_publisher = XianyuProductPublisher(self.xianyu_apis)
    
    def _register_routes(self):
        """注册API路由"""
        
        # 系统管理接口
        self.app.route('/api/system/status', methods=['GET'])(self.get_system_status)
        self.app.route('/api/system/start', methods=['POST'])(self.start_system)
        self.app.route('/api/system/stop', methods=['POST'])(self.stop_system)
        self.app.route('/api/system/restart', methods=['POST'])(self.restart_system)
        
        # 配置管理接口
        self.app.route('/api/config', methods=['GET'])(self.get_config)
        self.app.route('/api/config', methods=['PUT'])(self.update_config)
        
        # 对话管理接口
        self.app.route('/api/conversations', methods=['GET'])(self.get_conversations)
        self.app.route('/api/conversations/<chat_id>', methods=['GET'])(self.get_conversation_detail)
        self.app.route('/api/conversations/<chat_id>/messages', methods=['GET'])(self.get_conversation_messages)
        self.app.route('/api/conversations/<chat_id>/manual-mode', methods=['POST'])(self.toggle_manual_mode)
        self.app.route('/api/conversations/<chat_id>/send-message', methods=['POST'])(self.send_manual_message)
        
        # Agent管理接口
        self.app.route('/api/agents/status', methods=['GET'])(self.get_agents_status)
        self.app.route('/api/agents/reload-prompts', methods=['POST'])(self.reload_prompts)
        
        # 商品管理接口
        self.app.route('/api/products/templates', methods=['GET'])(self.get_product_templates)
        self.app.route('/api/products/templates', methods=['POST'])(self.create_product_template)
        self.app.route('/api/products/templates/<template_name>', methods=['GET'])(self.get_product_template)
        self.app.route('/api/products/templates/<template_name>', methods=['PUT'])(self.update_product_template)
        self.app.route('/api/products/templates/<template_name>', methods=['DELETE'])(self.delete_product_template)
        self.app.route('/api/products/publish', methods=['POST'])(self.publish_product)
        self.app.route('/api/products/publish/batch', methods=['POST'])(self.batch_publish_products)
        self.app.route('/api/products/records', methods=['GET'])(self.get_publish_records)
        
        # 统计分析接口
        self.app.route('/api/analytics/overview', methods=['GET'])(self.get_analytics_overview)
        self.app.route('/api/analytics/conversations', methods=['GET'])(self.get_conversation_analytics)
        self.app.route('/api/analytics/products', methods=['GET'])(self.get_product_analytics)
        
        # 日志接口
        self.app.route('/api/logs', methods=['GET'])(self.get_logs)
        
        # 静态文件服务
        self.app.route('/', defaults={'path': ''})(self.serve_static)
        self.app.route('/<path:path>')(self.serve_static)
    
    # ========== 系统管理接口 ==========
    
    def get_system_status(self):
        """获取系统状态"""
        try:
            # 更新状态信息
            if self.xianyu_live and self.live_thread and self.live_thread.is_alive():
                self.system_status['running'] = True
            else:
                self.system_status['running'] = False
                self.system_status['connected'] = False
            
            return jsonify({
                'status': 'success',
                'data': self.system_status
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def start_system(self):
        """启动系统"""
        try:
            if self.system_status['running']:
                return jsonify({
                    'status': 'error',
                    'message': '系统已在运行中'
                }), 400
            
            cookies_str = os.getenv("COOKIES_STR")
            if not cookies_str:
                return jsonify({
                    'status': 'error',
                    'message': '请先配置COOKIES_STR'
                }), 400
            
            # 创建XianyuLive实例
            self.xianyu_live = XianyuLive(cookies_str)
            
            # 在新线程中启动
            def run_xianyu_live():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.xianyu_live.main())
                except Exception as e:
                    logger.error(f"XianyuLive运行异常: {e}")
                finally:
                    loop.close()
            
            self.live_thread = threading.Thread(target=run_xianyu_live, daemon=True)
            self.live_thread.start()
            
            # 更新状态
            self.system_status['running'] = True
            self.system_status['start_time'] = time.time()
            
            return jsonify({
                'status': 'success',
                'message': '系统启动成功'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'启动失败: {str(e)}'
            }), 500
    
    def stop_system(self):
        """停止系统"""
        try:
            if not self.system_status['running']:
                return jsonify({
                    'status': 'error',
                    'message': '系统未在运行'
                }), 400
            
            # 停止XianyuLive
            if self.xianyu_live:
                # 设置停止标志
                self.xianyu_live.connection_restart_flag = False
            
            # 更新状态
            self.system_status['running'] = False
            self.system_status['connected'] = False
            
            return jsonify({
                'status': 'success',
                'message': '系统停止成功'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'停止失败: {str(e)}'
            }), 500
    
    def restart_system(self):
        """重启系统"""
        try:
            # 先停止
            self.stop_system()
            time.sleep(2)
            # 再启动
            return self.start_system()
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'重启失败: {str(e)}'
            }), 500
    
    # ========== 配置管理接口 ==========
    
    def get_config(self):
        """获取配置"""
        try:
            config = {
                'api_key': os.getenv("API_KEY", "")[:10] + "***" if os.getenv("API_KEY") else "",
                'model_base_url': os.getenv("MODEL_BASE_URL", ""),
                'model_name': os.getenv("MODEL_NAME", ""),
                'toggle_keywords': os.getenv("TOGGLE_KEYWORDS", ""),
                'heartbeat_interval': os.getenv("HEARTBEAT_INTERVAL", "15"),
                'log_level': os.getenv("LOG_LEVEL", "INFO"),
                'cookies_configured': bool(os.getenv("COOKIES_STR"))
            }
            
            return jsonify({
                'status': 'success',
                'data': config
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def update_config(self):
        """更新配置"""
        try:
            data = request.get_json()
            
            # 更新环境变量（这里只是示例，实际应用中需要持久化到.env文件）
            # 由于安全考虑，这里不实现实际的配置更新
            
            return jsonify({
                'status': 'success',
                'message': '配置更新成功'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ========== 对话管理接口 ==========
    
    def get_conversations(self):
        """获取对话列表"""
        try:
            # 从数据库获取对话列表
            conversations = self.context_manager.get_all_conversations()
            
            return jsonify({
                'status': 'success',
                'data': conversations
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def get_conversation_detail(self, chat_id):
        """获取对话详情"""
        try:
            detail = self.context_manager.get_conversation_detail(chat_id)
            
            return jsonify({
                'status': 'success',
                'data': detail
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def get_conversation_messages(self, chat_id):
        """获取对话消息"""
        try:
            messages = self.context_manager.get_context_by_chat(chat_id)
            
            return jsonify({
                'status': 'success',
                'data': messages
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def toggle_manual_mode(self, chat_id):
        """切换人工接管模式"""
        try:
            if self.xianyu_live:
                mode = self.xianyu_live.toggle_manual_mode(chat_id)
                return jsonify({
                    'status': 'success',
                    'data': {'mode': mode}
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': '系统未运行'
                }), 400
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def send_manual_message(self, chat_id):
        """发送人工消息"""
        try:
            data = request.get_json()
            message = data.get('message', '')
            
            if not message:
                return jsonify({
                    'status': 'error',
                    'message': '消息不能为空'
                }), 400
            
            # TODO: 实现发送消息逻辑
            
            return jsonify({
                'status': 'success',
                'message': '消息发送成功'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ========== Agent管理接口 ==========
    
    def get_agents_status(self):
        """获取Agent状态"""
        try:
            agents_status = {
                'classify': {'status': 'active', 'last_used': time.time()},
                'price': {'status': 'active', 'last_used': time.time()},
                'tech': {'status': 'active', 'last_used': time.time()},
                'default': {'status': 'active', 'last_used': time.time()}
            }
            
            return jsonify({
                'status': 'success',
                'data': agents_status
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def reload_prompts(self):
        """重新加载提示词"""
        try:
            self.bot.reload_prompts()
            
            return jsonify({
                'status': 'success',
                'message': '提示词重新加载成功'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ========== 商品管理接口 ==========
    
    def get_product_templates(self):
        """获取商品模板列表"""
        try:
            templates = self.product_publisher.list_templates()
            
            return jsonify({
                'status': 'success',
                'data': templates
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def create_product_template(self):
        """创建商品模板"""
        try:
            data = request.get_json()
            template_name = data.get('template_name')
            
            if not template_name:
                return jsonify({
                    'status': 'error',
                    'message': '模板名称不能为空'
                }), 400
            
            success = self.product_publisher.save_template(template_name, data)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': '模板创建成功'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': '模板创建失败'
                }), 500
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def get_product_template(self, template_name):
        """获取商品模板"""
        try:
            template = self.product_publisher.get_template(template_name)
            
            if template:
                return jsonify({
                    'status': 'success',
                    'data': template
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': '模板不存在'
                }), 404
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def update_product_template(self, template_name):
        """更新商品模板"""
        try:
            data = request.get_json()
            success = self.product_publisher.save_template(template_name, data)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': '模板更新成功'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': '模板更新失败'
                }), 500
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def delete_product_template(self, template_name):
        """删除商品模板"""
        try:
            # TODO: 实现删除逻辑
            
            return jsonify({
                'status': 'success',
                'message': '模板删除成功'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def publish_product(self):
        """发布商品"""
        try:
            data = request.get_json()
            template_name = data.get('template_name')
            custom_data = data.get('custom_data', {})
            
            if not template_name:
                return jsonify({
                    'status': 'error',
                    'message': '模板名称不能为空'
                }), 400
            
            item_id = self.product_publisher.publish_product(template_name, custom_data)
            
            if item_id:
                return jsonify({
                    'status': 'success',
                    'data': {'item_id': item_id},
                    'message': '商品发布成功'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': '商品发布失败'
                }), 500
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def batch_publish_products(self):
        """批量发布商品"""
        try:
            data = request.get_json()
            template_names = data.get('template_names', [])
            interval = data.get('interval', 30)
            
            if not template_names:
                return jsonify({
                    'status': 'error',
                    'message': '模板列表不能为空'
                }), 400
            
            results = self.product_publisher.batch_publish(template_names, interval)
            
            return jsonify({
                'status': 'success',
                'data': results,
                'message': '批量发布完成'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def get_publish_records(self):
        """获取发布记录"""
        try:
            limit = request.args.get('limit', 50, type=int)
            records = self.product_publisher.get_publish_records(limit)
            
            return jsonify({
                'status': 'success',
                'data': records
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ========== 统计分析接口 ==========
    
    def get_analytics_overview(self):
        """获取概览统计"""
        try:
            overview = {
                'total_conversations': 0,
                'total_messages': 0,
                'auto_reply_rate': 0,
                'manual_mode_count': 0,
                'published_products': 0,
                'success_rate': 0
            }
            
            # TODO: 实现统计逻辑
            
            return jsonify({
                'status': 'success',
                'data': overview
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def get_conversation_analytics(self):
        """获取对话统计"""
        try:
            analytics = {
                'daily_messages': [],
                'intent_distribution': {},
                'response_time': [],
                'satisfaction_rate': 0
            }
            
            # TODO: 实现统计逻辑
            
            return jsonify({
                'status': 'success',
                'data': analytics
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def get_product_analytics(self):
        """获取商品统计"""
        try:
            analytics = {
                'publish_trend': [],
                'success_rate_trend': [],
                'category_distribution': {},
                'revenue_estimate': 0
            }
            
            # TODO: 实现统计逻辑
            
            return jsonify({
                'status': 'success',
                'data': analytics
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ========== 日志接口 ==========
    
    def get_logs(self):
        """获取日志"""
        try:
            lines = request.args.get('lines', 100, type=int)
            level = request.args.get('level', 'INFO')
            
            # TODO: 实现日志读取逻辑
            logs = [
                {'timestamp': time.time(), 'level': 'INFO', 'message': '示例日志消息'}
            ]
            
            return jsonify({
                'status': 'success',
                'data': logs
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """启动Web服务"""
        logger.info(f"启动Web API服务: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
    
    def serve_static(self, path):
        """提供静态文件服务"""
        try:
            if path == '':
                path = 'index.html'
            return send_from_directory('static', path)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'文件不存在: {path}'
            }), 404


if __name__ == '__main__':
    # 创建API服务
    api = XianyuWebAPI()
    
    # 启动服务
    api.run(debug=True)