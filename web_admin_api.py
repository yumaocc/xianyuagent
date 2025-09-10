# -*- coding: utf-8 -*-
"""
XianyuAutoAgent Web Admin API 适配器
为前端管理界面提供完整的 RESTful API 接口
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import os
import time
import glob
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

# 导入原有组件
from web_api import XianyuWebAPI
from product_prompt_manager import ProductPromptManager

class WebAdminAPI(XianyuWebAPI):
    """Web管理端API适配器"""
    
    def __init__(self):
        super().__init__()
        # 初始化提示词管理器
        self.prompt_manager = ProductPromptManager()
        # 注册管理端专用路由
        self._register_admin_routes()
    
    def _register_admin_routes(self):
        """注册管理端专用路由"""
        
        # 认证接口
        self.app.route('/api/auth/login', methods=['POST'])(self.admin_login)
        self.app.route('/api/auth/logout', methods=['POST'])(self.admin_logout)
        self.app.route('/api/auth/me', methods=['GET'])(self.get_current_user)
        
        # 系统统计接口
        self.app.route('/api/system/stats', methods=['GET'])(self.get_system_stats)
        self.app.route('/api/system/health', methods=['GET'])(self.get_system_health)
        self.app.route('/api/system/notifications', methods=['GET'])(self.get_notifications)
        
        # 商品管理接口（新增）
        self.app.route('/api/products', methods=['GET'])(self.get_products)
        self.app.route('/api/products', methods=['POST'])(self.create_product)
        self.app.route('/api/products/<product_id>', methods=['GET'])(self.get_product)
        self.app.route('/api/products/<product_id>', methods=['PUT'])(self.update_product)
        self.app.route('/api/products/<product_id>', methods=['DELETE'])(self.delete_product)
        
        # 提示词管理接口
        self.app.route('/api/products/<product_id>/prompts', methods=['GET'])(self.get_product_prompts)
        self.app.route('/api/products/<product_id>/prompts', methods=['PUT'])(self.update_product_prompt)
        self.app.route('/api/products/<product_id>/prompts/batch', methods=['PUT'])(self.batch_update_prompts)
        self.app.route('/api/prompts/preview', methods=['POST'])(self.preview_prompt)
        self.app.route('/api/prompts/validate', methods=['POST'])(self.validate_prompt)
        self.app.route('/api/prompts/templates', methods=['GET'])(self.get_prompt_templates)
        
        # 同步管理接口
        self.app.route('/api/sync/status', methods=['GET'])(self.get_sync_status)
        self.app.route('/api/sync/history', methods=['GET'])(self.get_sync_history)
        self.app.route('/api/sync/manual', methods=['POST'])(self.trigger_manual_sync)
        self.app.route('/api/sync/auto', methods=['GET'])(self.get_auto_sync_settings)
        self.app.route('/api/sync/auto', methods=['POST'])(self.update_auto_sync_settings)
        self.app.route('/api/sync/test-connection', methods=['POST'])(self.test_connection)
        
        # 闲鱼商品拉取接口
        self.app.route('/api/xianyu/items', methods=['GET'])(self.get_xianyu_items)
        self.app.route('/api/xianyu/items/<item_id>', methods=['GET'])(self.get_xianyu_item)
        self.app.route('/api/xianyu/sync', methods=['POST'])(self.sync_from_xianyu)
        
        # Cookie 配置管理接口
        self.app.route('/api/config/cookies', methods=['GET'])(self.get_cookie_config)
        self.app.route('/api/config/cookies', methods=['POST'])(self.update_cookie_config)
        self.app.route('/api/config/cookies/test', methods=['POST'])(self.test_cookie_connection)
    
    # ========== 认证接口 ==========
    
    def admin_login(self):
        """管理员登录"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            # 简单的认证逻辑（实际应用中应使用更安全的方式）
            if username == 'admin' and password == '123456':
                return jsonify({
                    'success': True,
                    'data': {
                        'token': 'admin-token-' + str(int(time.time())),
                        'user': {
                            'id': '1',
                            'username': 'admin',
                            'email': 'admin@xianyu.com',
                            'role': 'admin',
                            'createdAt': '2024-01-01T00:00:00Z'
                        },
                        'expiresIn': 86400
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '用户名或密码错误'
                }), 401
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def admin_logout(self):
        """管理员登出"""
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
    
    def get_current_user(self):
        """获取当前用户信息"""
        return jsonify({
            'success': True,
            'data': {
                'id': '1',
                'username': 'admin',
                'email': 'admin@xianyu.com',
                'role': 'admin',
                'createdAt': '2024-01-01T00:00:00Z'
            }
        })
    
    # ========== 系统统计接口 ==========
    
    def get_system_stats(self):
        """获取系统统计信息"""
        try:
            # 获取产品数量统计
            product_files = glob.glob('./prompts/products/*_config.json')
            total_products = len(product_files)
            
            # 计算配置完成度
            configured_products = 0
            total_value = 0
            
            for config_file in product_files:
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        if config.get('prompts_configured'):
                            configured_products += 1
                        if config.get('price'):
                            total_value += float(config['price'])
                except:
                    continue
            
            ai_config_rate = (configured_products / total_products * 100) if total_products > 0 else 0
            
            stats = {
                'totalProducts': total_products,
                'totalValue': round(total_value, 2),
                'aiConfigRate': round(ai_config_rate, 1),
                'todaySyncCount': 0,  # 从同步记录获取
                'activeProducts': configured_products,
                'errorCount': 0
            }
            
            return jsonify({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def get_system_health(self):
        """获取系统健康状态"""
        try:
            health = {
                'status': 'healthy',
                'services': [
                    {'name': 'XianyuAPI', 'status': 'up', 'responseTime': 45},
                    {'name': 'AI模型', 'status': 'up', 'responseTime': 120},
                    {'name': '数据库', 'status': 'up', 'responseTime': 15}
                ],
                'uptime': int(time.time() - (self.system_status.get('start_time') or time.time())),
                'version': '1.0.0'
            }
            
            return jsonify({
                'success': True,
                'data': health
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def get_notifications(self):
        """获取系统通知"""
        try:
            # 返回空通知列表（可根据需要扩展）
            notifications = {
                'list': [],
                'total': 0,
                'unreadCount': 0
            }
            
            return jsonify({
                'success': True,
                'data': notifications
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    # ========== 商品管理接口 ==========
    
    def get_products(self):
        """获取商品列表"""
        try:
            page = request.args.get('page', 1, type=int)
            pageSize = request.args.get('pageSize', 20, type=int)
            keyword = request.args.get('keyword', '')
            category = request.args.get('category', '')
            status = request.args.get('status', '')
            
            # 获取所有产品配置文件
            config_files = glob.glob('./prompts/products/*_config.json')
            products = []
            
            for config_file in config_files:
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        
                        # 构造产品数据
                        product_id = os.path.basename(config_file).replace('_config.json', '')
                        product = {
                            'id': product_id,
                            'itemId': config.get('item_id', product_id),
                            'title': config.get('title', '未命名商品'),
                            'desc': config.get('description', ''),
                            'price': float(config.get('price', 0)),
                            'soldPrice': float(config.get('sold_price', config.get('price', 0))),
                            'category': config.get('category', '未分类'),
                            'status': 'active' if config.get('prompts_configured') else 'draft',
                            'createdAt': config.get('created_at', datetime.now().isoformat()),
                            'updatedAt': config.get('updated_at', datetime.now().isoformat()),
                            'hasCustomPrompts': config.get('prompts_configured', False),
                            'syncStatus': 'synced' if config.get('prompts_configured') else 'pending'
                        }
                        
                        # 应用筛选条件
                        if keyword and keyword.lower() not in product['title'].lower():
                            continue
                        if category and product['category'] != category:
                            continue
                        if status and product['status'] != status:
                            continue
                        
                        products.append(product)
                        
                except Exception as e:
                    logger.warning(f"解析配置文件失败 {config_file}: {e}")
                    continue
            
            # 分页
            total = len(products)
            start = (page - 1) * pageSize
            end = start + pageSize
            products = products[start:end]
            
            return jsonify({
                'success': True,
                'data': {
                    'list': products,
                    'total': total,
                    'page': page,
                    'pageSize': pageSize
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def get_product(self, product_id):
        """获取商品详情"""
        try:
            config_file = f'./prompts/products/{product_id}_config.json'
            
            if not os.path.exists(config_file):
                return jsonify({
                    'success': False,
                    'message': '商品不存在'
                }), 404
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            product = {
                'id': product_id,
                'itemId': config.get('item_id', product_id),
                'title': config.get('title', '未命名商品'),
                'desc': config.get('description', ''),
                'price': float(config.get('price', 0)),
                'soldPrice': float(config.get('sold_price', config.get('price', 0))),
                'category': config.get('category', '未分类'),
                'status': 'active' if config.get('prompts_configured') else 'draft',
                'createdAt': config.get('created_at', datetime.now().isoformat()),
                'updatedAt': config.get('updated_at', datetime.now().isoformat()),
                'hasCustomPrompts': config.get('prompts_configured', False),
                'syncStatus': 'synced' if config.get('prompts_configured') else 'pending'
            }
            
            return jsonify({
                'success': True,
                'data': product
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def create_product(self):
        """创建商品"""
        try:
            data = request.get_json()
            
            product_id = data.get('itemId')
            if not product_id:
                return jsonify({
                    'success': False,
                    'message': '商品ID不能为空'
                }), 400
            
            # 检查是否已存在
            config_file = f'./prompts/products/{product_id}_config.json'
            if os.path.exists(config_file):
                return jsonify({
                    'success': False,
                    'message': '商品ID已存在'
                }), 400
            
            # 创建配置文件
            config = {
                'item_id': product_id,
                'title': data.get('title', ''),
                'description': data.get('desc', ''),
                'price': str(data.get('price', 0)),
                'category': data.get('category', '未分类'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'prompts_configured': False
            }
            
            # 创建目录
            os.makedirs('./prompts/products', exist_ok=True)
            
            # 保存配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 创建提示词文件
            for prompt_type in ['default', 'price', 'tech']:
                prompt_file = f'./prompts/products/{product_id}_{prompt_type}.txt'
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(f'# {product_id} - {prompt_type} 提示词\n\n这里是{prompt_type}提示词内容...')
            
            # 返回创建的产品
            product = {
                'id': product_id,
                'itemId': product_id,
                'title': config['title'],
                'desc': config['description'],
                'price': float(config['price']),
                'category': config['category'],
                'status': 'draft',
                'createdAt': config['created_at'],
                'updatedAt': config['updated_at'],
                'hasCustomPrompts': False,
                'syncStatus': 'pending'
            }
            
            return jsonify({
                'success': True,
                'data': product
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def update_product(self, product_id):
        """更新商品"""
        try:
            data = request.get_json()
            config_file = f'./prompts/products/{product_id}_config.json'
            
            if not os.path.exists(config_file):
                return jsonify({
                    'success': False,
                    'message': '商品不存在'
                }), 404
            
            # 读取现有配置
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新配置
            if 'title' in data:
                config['title'] = data['title']
            if 'desc' in data:
                config['description'] = data['desc']
            if 'price' in data:
                config['price'] = str(data['price'])
            if 'category' in data:
                config['category'] = data['category']
            
            config['updated_at'] = datetime.now().isoformat()
            
            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'message': '商品更新成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def delete_product(self, product_id):
        """删除商品"""
        try:
            # 删除相关文件
            files_to_delete = [
                f'./prompts/products/{product_id}_config.json',
                f'./prompts/products/{product_id}_default.txt',
                f'./prompts/products/{product_id}_price.txt',
                f'./prompts/products/{product_id}_tech.txt'
            ]
            
            deleted_files = 0
            for file_path in files_to_delete:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files += 1
            
            if deleted_files > 0:
                return jsonify({
                    'success': True,
                    'message': '商品删除成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '商品不存在'
                }), 404
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    # ========== 提示词管理接口 ==========
    
    def get_product_prompts(self, product_id):
        """获取商品提示词"""
        try:
            prompts = {}
            
            for prompt_type in ['default', 'price', 'tech', 'classify']:
                prompt_file = f'./prompts/products/{product_id}_{prompt_type}.txt'
                if os.path.exists(prompt_file):
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        prompts[prompt_type] = f.read()
                else:
                    prompts[prompt_type] = f'# {product_id} - {prompt_type} 提示词\n\n'
            
            return jsonify({
                'success': True,
                'data': prompts
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def update_product_prompt(self, product_id):
        """更新商品提示词"""
        try:
            data = request.get_json()
            prompt_type = data.get('type')
            content = data.get('content', '')
            
            if not prompt_type:
                return jsonify({
                    'success': False,
                    'message': '提示词类型不能为空'
                }), 400
            
            # 创建目录
            os.makedirs('./prompts/products', exist_ok=True)
            
            # 保存提示词文件
            prompt_file = f'./prompts/products/{product_id}_{prompt_type}.txt'
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新配置文件中的状态
            config_file = f'./prompts/products/{product_id}_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                config['prompts_configured'] = True
                config['updated_at'] = datetime.now().isoformat()
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'message': '提示词更新成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def batch_update_prompts(self, product_id):
        """批量更新提示词"""
        try:
            data = request.get_json()
            
            # 创建目录
            os.makedirs('./prompts/products', exist_ok=True)
            
            # 更新每个提示词
            for prompt_type, content in data.items():
                if prompt_type in ['default', 'price', 'tech', 'classify']:
                    prompt_file = f'./prompts/products/{product_id}_{prompt_type}.txt'
                    with open(prompt_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            # 更新配置状态
            config_file = f'./prompts/products/{product_id}_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                config['prompts_configured'] = True
                config['updated_at'] = datetime.now().isoformat()
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'message': '批量更新成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def preview_prompt(self):
        """预览提示词效果"""
        try:
            data = request.get_json()
            prompt_type = data.get('type')
            content = data.get('content', '')
            product_info = data.get('productInfo', {})
            
            # 简单的变量替换预览
            preview = content
            variables = {}
            
            # 替换变量
            for key, value in product_info.items():
                placeholder = f'{{{key}}}'
                if placeholder in content:
                    preview = preview.replace(placeholder, str(value))
                    variables[key] = str(value)
            
            return jsonify({
                'success': True,
                'data': {
                    'preview': preview,
                    'variables': variables,
                    'wordCount': len(preview)
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def validate_prompt(self):
        """验证提示词语法"""
        try:
            data = request.get_json()
            content = data.get('content', '')
            prompt_type = data.get('type')
            
            # 简单的语法验证
            errors = []
            warnings = []
            suggestions = []
            
            # 检查是否包含必要变量
            if '{title}' not in content:
                warnings.append('建议包含商品标题变量 {title}')
            if '{price}' not in content and prompt_type == 'price':
                errors.append('价格提示词必须包含价格变量 {price}')
            
            # 检查内容长度
            if len(content) < 10:
                errors.append('提示词内容过短')
            elif len(content) > 2000:
                warnings.append('提示词内容较长，可能影响处理效率')
            
            return jsonify({
                'success': True,
                'data': {
                    'valid': len(errors) == 0,
                    'errors': errors,
                    'warnings': warnings,
                    'suggestions': suggestions
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def get_prompt_templates(self):
        """获取提示词模板"""
        try:
            # 读取默认模板
            templates = []
            template_files = glob.glob('./prompts/*_prompt*.txt')
            
            for template_file in template_files:
                filename = os.path.basename(template_file)
                if 'optimized' in filename:
                    continue
                
                # 解析模板类型
                prompt_type = 'default'
                if 'price' in filename:
                    prompt_type = 'price'
                elif 'tech' in filename:
                    prompt_type = 'tech'
                elif 'classify' in filename:
                    prompt_type = 'classify'
                
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    template = {
                        'id': filename.replace('.txt', ''),
                        'name': f'{prompt_type.title()} 默认模板',
                        'type': prompt_type,
                        'content': content,
                        'description': f'{prompt_type}类型的默认提示词模板',
                        'isDefault': True,
                        'createdAt': datetime.now().isoformat(),
                        'updatedAt': datetime.now().isoformat()
                    }
                    
                    templates.append(template)
                    
                except Exception as e:
                    logger.warning(f"读取模板文件失败 {template_file}: {e}")
                    continue
            
            return jsonify({
                'success': True,
                'data': templates
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    # ========== 同步管理接口 ==========
    
    def get_sync_status(self):
        """获取同步状态"""
        try:
            # 模拟同步状态
            sync_status = {
                'id': f'sync_{int(time.time())}',
                'status': 'completed',  # pending, running, completed, error
                'progress': 100,
                'message': '同步完成',
                'startTime': datetime.now().isoformat(),
                'endTime': datetime.now().isoformat(),
                'affectedItems': 5
            }
            
            return jsonify({
                'success': True,
                'data': sync_status
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def get_sync_history(self):
        """获取同步历史"""
        try:
            page = request.args.get('page', 1, type=int)
            pageSize = request.args.get('pageSize', 10, type=int)
            
            # 模拟同步历史数据
            history_items = []
            for i in range(pageSize):
                history_items.append({
                    'id': f'sync_{int(time.time())}_{i}',
                    'status': 'completed',
                    'startTime': datetime.now().isoformat(),
                    'endTime': datetime.now().isoformat(),
                    'affectedItems': 5 + i,
                    'message': '同步完成'
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'list': history_items,
                    'total': 50,  # 模拟总数
                    'page': page,
                    'pageSize': pageSize
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def trigger_manual_sync(self):
        """触发手动同步"""
        try:
            data = request.get_json()
            item_ids = data.get('itemIds', [])
            
            # 模拟同步触发
            sync_id = f'sync_{int(time.time())}'
            
            return jsonify({
                'success': True,
                'data': {
                    'syncId': sync_id,
                    'message': f'同步任务已启动，涉及{len(item_ids)}个商品'
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def get_auto_sync_settings(self):
        """获取自动同步设置"""
        try:
            settings = {
                'enabled': True,
                'interval': 60,  # 分钟
                'lastSync': datetime.now().isoformat(),
                'nextSync': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'data': settings
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def update_auto_sync_settings(self):
        """更新自动同步设置"""
        try:
            data = request.get_json()
            # 这里可以保存到配置文件
            
            return jsonify({
                'success': True,
                'message': '自动同步设置已更新'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def test_connection(self):
        """测试连接"""
        try:
            # 模拟连接测试
            return jsonify({
                'success': True,
                'data': {
                    'connected': True,
                    'latency': 45,
                    'version': '1.0.0',
                    'message': '连接正常'
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    # ========== 闲鱼商品拉取接口 ==========
    
    def get_xianyu_items(self):
        """获取闲鱼商品列表"""
        try:
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('pageSize', 20, type=int)
            status = request.args.get('status', 'ALL')
            
            # 调用闲鱼API获取商品列表
            result = self.xianyu_apis.get_user_items(page, page_size, status)
            
            if 'error' in result:
                return jsonify({
                    'success': False,
                    'message': result['error']
                }), 500
            
            # 解析响应数据
            if 'data' in result and result['data']:
                items_data = result['data']
                items = []
                
                # 解析商品列表
                if 'items' in items_data:
                    for item in items_data['items']:
                        items.append({
                            'itemId': item.get('itemId', ''),
                            'title': item.get('title', ''),
                            'price': item.get('price', 0),
                            'status': item.get('status', ''),
                            'publishTime': item.get('publishTime', ''),
                            'viewCount': item.get('viewCount', 0),
                            'likeCount': item.get('likeCount', 0),
                            'images': item.get('images', []),
                            'category': item.get('category', ''),
                            'location': item.get('location', ''),
                        })
                
                return jsonify({
                    'success': True,
                    'data': {
                        'list': items,
                        'total': items_data.get('total', len(items)),
                        'page': page,
                        'pageSize': page_size
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'data': {
                        'list': [],
                        'total': 0,
                        'page': page,
                        'pageSize': page_size
                    }
                })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def get_xianyu_item(self, item_id):
        """获取闲鱼单个商品详情"""
        try:
            # 调用闲鱼API获取商品详情
            result = self.xianyu_apis.get_item_info(item_id)
            
            if 'error' in result:
                return jsonify({
                    'success': False,
                    'message': result['error']
                }), 500
            
            # 解析响应数据
            if 'data' in result and 'itemDO' in result['data']:
                item_data = result['data']['itemDO']
                
                item = {
                    'itemId': item_data.get('itemId', ''),
                    'title': item_data.get('title', ''),
                    'description': item_data.get('description', ''),
                    'price': item_data.get('price', 0),
                    'originalPrice': item_data.get('originalPrice', 0),
                    'status': item_data.get('status', ''),
                    'publishTime': item_data.get('publishTime', ''),
                    'viewCount': item_data.get('viewCount', 0),
                    'likeCount': item_data.get('likeCount', 0),
                    'images': item_data.get('images', []),
                    'category': item_data.get('category', ''),
                    'location': item_data.get('location', ''),
                    'tags': item_data.get('tags', []),
                    'condition': item_data.get('condition', ''),
                }
                
                return jsonify({
                    'success': True,
                    'data': item
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '商品不存在或已下架'
                }), 404
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def sync_from_xianyu(self):
        """从闲鱼同步商品到本地"""
        try:
            data = request.get_json()
            item_ids = data.get('itemIds', [])
            sync_all = data.get('syncAll', False)
            
            synced_items = []
            failed_items = []
            
            if sync_all:
                # 同步所有商品
                page = 1
                page_size = 50
                
                while True:
                    result = self.xianyu_apis.get_user_items(page, page_size, 'ALL')
                    
                    if 'error' in result:
                        break
                    
                    if 'data' not in result or not result['data'].get('items'):
                        break
                    
                    items = result['data']['items']
                    
                    for item in items:
                        item_id = item.get('itemId')
                        if item_id:
                            success = self._sync_single_item(item_id, item)
                            if success:
                                synced_items.append(item_id)
                            else:
                                failed_items.append(item_id)
                    
                    # 检查是否还有下一页
                    if len(items) < page_size:
                        break
                    page += 1
                    
                    # 防止死循环，最多同步10页
                    if page > 10:
                        break
            else:
                # 同步指定商品
                for item_id in item_ids:
                    # 先获取详细信息
                    item_result = self.xianyu_apis.get_item_info(item_id)
                    
                    if 'error' not in item_result and 'data' in item_result:
                        item_data = item_result['data'].get('itemDO', {})
                        success = self._sync_single_item(item_id, item_data)
                        
                        if success:
                            synced_items.append(item_id)
                        else:
                            failed_items.append(item_id)
                    else:
                        failed_items.append(item_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'syncedItems': synced_items,
                    'failedItems': failed_items,
                    'syncedCount': len(synced_items),
                    'failedCount': len(failed_items),
                    'message': f'成功同步 {len(synced_items)} 个商品，失败 {len(failed_items)} 个'
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def _sync_single_item(self, item_id, item_data):
        """同步单个商品"""
        try:
            # 检查商品是否已存在
            config_file = f'./prompts/products/{item_id}_config.json'
            
            # 构造商品配置
            config = {
                'item_id': item_id,
                'title': item_data.get('title', '未命名商品'),
                'description': item_data.get('description', ''),
                'price': str(item_data.get('price', 0)),
                'original_price': str(item_data.get('originalPrice', item_data.get('price', 0))),
                'category': item_data.get('category', '未分类'),
                'status': item_data.get('status', 'draft'),
                'publish_time': item_data.get('publishTime', ''),
                'view_count': item_data.get('viewCount', 0),
                'like_count': item_data.get('likeCount', 0),
                'images': item_data.get('images', []),
                'location': item_data.get('location', ''),
                'tags': item_data.get('tags', []),
                'condition': item_data.get('condition', ''),
                'synced_from_xianyu': True,
                'sync_time': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'prompts_configured': False
            }
            
            # 如果已存在，则更新同步时间
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                
                # 保留提示词配置状态
                config['prompts_configured'] = existing_config.get('prompts_configured', False)
                config['created_at'] = existing_config.get('created_at', config['created_at'])
            
            # 创建目录
            os.makedirs('./prompts/products', exist_ok=True)
            
            # 保存配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 如果是新商品，创建默认提示词文件
            if not os.path.exists(config_file) or not config['prompts_configured']:
                for prompt_type in ['default', 'price', 'tech', 'classify']:
                    prompt_file = f'./prompts/products/{item_id}_{prompt_type}.txt'
                    if not os.path.exists(prompt_file):
                        with open(prompt_file, 'w', encoding='utf-8') as f:
                            f.write(f'# {item_id} - {prompt_type} 提示词\n\n')
            
            logger.info(f"商品同步成功: {item_id} - {config['title']}")
            return True
            
        except Exception as e:
            logger.error(f"同步商品失败 {item_id}: {str(e)}")
            return False
    
    # ========== Cookie 配置管理接口 ==========
    
    def get_cookie_config(self):
        """获取当前 Cookie 配置信息"""
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            cookies_str = os.getenv('COOKIES_STR', '')
            
            # 解析 Cookie 信息（隐藏敏感信息）
            if cookies_str:
                # 提取关键字段以验证 Cookie 的有效性
                key_cookies = ['unb', 'cookie2', '_m_h5_tk', 'cna']
                parsed_cookies = {}
                
                for cookie_pair in cookies_str.split(';'):
                    if '=' in cookie_pair:
                        key, value = cookie_pair.strip().split('=', 1)
                        if key in key_cookies:
                            # 只显示前几位和后几位，中间用*替代
                            if len(value) > 8:
                                parsed_cookies[key] = value[:4] + '*' * (len(value) - 8) + value[-4:]
                            else:
                                parsed_cookies[key] = '*' * len(value)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'hasCookies': True,
                        'cookiePreview': parsed_cookies,
                        'lastUpdated': self._get_env_file_modified_time(),
                        'status': 'configured'
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'data': {
                        'hasCookies': False,
                        'cookiePreview': {},
                        'lastUpdated': None,
                        'status': 'not_configured'
                    }
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def update_cookie_config(self):
        """更新 Cookie 配置"""
        try:
            data = request.get_json()
            cookies_str = data.get('cookiesStr', '').strip()
            
            if not cookies_str:
                return jsonify({
                    'success': False,
                    'message': 'Cookie 字符串不能为空'
                }), 400
            
            # 验证 Cookie 格式
            validation_result = self._validate_cookie_format(cookies_str)
            if not validation_result['valid']:
                return jsonify({
                    'success': False,
                    'message': validation_result['message']
                }), 400
            
            # 更新 .env 文件
            success = self._update_env_file('COOKIES_STR', cookies_str)
            
            if success:
                # 更新当前 session 的 cookies
                from utils.xianyu_utils import trans_cookies
                try:
                    cookies = trans_cookies(cookies_str)
                    self.xianyu_apis.session.cookies.update(cookies)
                    logger.info("Cookie 配置更新成功")
                except Exception as e:
                    logger.warning(f"更新 session cookies 失败: {e}")
                
                return jsonify({
                    'success': True,
                    'message': 'Cookie 配置更新成功',
                    'data': {
                        'updatedAt': datetime.now().isoformat(),
                        'status': 'configured'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '更新配置文件失败'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def test_cookie_connection(self):
        """测试 Cookie 连接"""
        try:
            data = request.get_json()
            cookies_str = data.get('cookiesStr', '')
            
            if not cookies_str:
                # 使用当前配置的 Cookie 进行测试
                import os
                from dotenv import load_dotenv
                load_dotenv()
                cookies_str = os.getenv('COOKIES_STR', '')
            
            if not cookies_str:
                return jsonify({
                    'success': False,
                    'message': '没有找到 Cookie 配置'
                }), 400
            
            # 创建临时 API 实例进行测试
            from XianyuApis import XianyuApis
            from utils.xianyu_utils import trans_cookies
            
            test_api = XianyuApis()
            try:
                cookies = trans_cookies(cookies_str)
                test_api.session.cookies.update(cookies)
                
                # 测试登录状态
                login_result = test_api.hasLogin()
                
                if login_result:
                    return jsonify({
                        'success': True,
                        'data': {
                            'connected': True,
                            'status': 'valid',
                            'message': 'Cookie 有效，连接成功',
                            'testTime': datetime.now().isoformat()
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'data': {
                            'connected': False,
                            'status': 'invalid',
                            'message': 'Cookie 已失效或无效',
                            'testTime': datetime.now().isoformat()
                        }
                    })
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'data': {
                        'connected': False,
                        'status': 'error',
                        'message': f'连接测试失败: {str(e)}',
                        'testTime': datetime.now().isoformat()
                    }
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def _validate_cookie_format(self, cookies_str):
        """验证 Cookie 格式"""
        try:
            # 检查基本格式
            if ';' not in cookies_str:
                return {'valid': False, 'message': 'Cookie 格式不正确，应包含多个键值对'}
            
            # 检查必要的字段
            required_fields = ['unb', 'cookie2']
            found_fields = []
            
            for cookie_pair in cookies_str.split(';'):
                if '=' in cookie_pair:
                    key = cookie_pair.strip().split('=')[0]
                    if key in required_fields:
                        found_fields.append(key)
            
            missing_fields = [field for field in required_fields if field not in found_fields]
            
            if missing_fields:
                return {
                    'valid': False, 
                    'message': f'缺少必要的 Cookie 字段: {", ".join(missing_fields)}'
                }
            
            return {'valid': True, 'message': 'Cookie 格式验证通过'}
            
        except Exception as e:
            return {'valid': False, 'message': f'Cookie 验证失败: {str(e)}'}
    
    def _update_env_file(self, key, value):
        """更新 .env 文件中的配置"""
        try:
            import re
            env_path = os.path.join(os.getcwd(), '.env')
            
            # 如果 .env 文件不存在，创建它
            if not os.path.exists(env_path):
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(f'{key}={value}\n')
                return True
            
            # 读取现有内容
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已存在该配置项
            pattern = rf'^{re.escape(key)}=.*$'
            if re.search(pattern, content, re.MULTILINE):
                # 更新现有配置
                new_content = re.sub(pattern, f'{key}={value}', content, flags=re.MULTILINE)
            else:
                # 添加新配置
                new_content = content.rstrip() + f'\n{key}={value}\n'
            
            # 写回文件
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
            
        except Exception as e:
            logger.error(f"更新 .env 文件失败: {e}")
            return False
    
    def _get_env_file_modified_time(self):
        """获取 .env 文件的修改时间"""
        try:
            env_path = os.path.join(os.getcwd(), '.env')
            if os.path.exists(env_path):
                mtime = os.path.getmtime(env_path)
                return datetime.fromtimestamp(mtime).isoformat()
        except:
            pass
        return None


if __name__ == '__main__':
    # 创建管理端API服务
    api = WebAdminAPI()
    
    # 启动服务
    api.run(host='0.0.0.0', port=5001, debug=True)