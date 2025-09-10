# -*- coding: utf-8 -*-
import json
import time
import os
import sqlite3
import base64
from typing import Dict, List, Optional, Union
from loguru import logger
from utils.xianyu_utils import generate_sign


class XianyuProductPublisher:
    """闲鱼商品发布管理器"""
    
    def __init__(self, xianyu_apis, db_path: str = "data/product_templates.db"):
        self.xianyu_apis = xianyu_apis
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建商品模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                category_id TEXT NOT NULL,
                images TEXT,  -- JSON数组，存储图片路径或URL
                tags TEXT,   -- JSON数组，存储标签
                location TEXT,  -- 地理位置
                condition_type INTEGER DEFAULT 1,  -- 商品状态：1=全新，2=九成新等
                trade_type INTEGER DEFAULT 1,      -- 交易方式：1=邮寄，2=自提等
                auto_publish BOOLEAN DEFAULT 0,   -- 是否自动发布
                publish_schedule TEXT,  -- 发布计划（JSON格式）
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建发布记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS publish_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                item_id TEXT,  -- 闲鱼商品ID
                publish_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success',  -- success, failed
                error_message TEXT,
                FOREIGN KEY (template_id) REFERENCES product_templates (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"商品发布数据库初始化完成: {self.db_path}")
    
    def save_template(self, template_name: str, product_data: Dict) -> bool:
        """保存商品模板"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 处理图片和标签数据
            images_json = json.dumps(product_data.get('images', []))
            tags_json = json.dumps(product_data.get('tags', []))
            schedule_json = json.dumps(product_data.get('publish_schedule', {}))
            
            cursor.execute('''
                INSERT OR REPLACE INTO product_templates 
                (template_name, title, description, price, category_id, images, tags, 
                 location, condition_type, trade_type, auto_publish, publish_schedule, updated_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                template_name,
                product_data['title'],
                product_data['description'], 
                product_data['price'],
                product_data['category_id'],
                images_json,
                tags_json,
                product_data.get('location', ''),
                product_data.get('condition_type', 1),
                product_data.get('trade_type', 1),
                product_data.get('auto_publish', False),
                schedule_json
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"商品模板保存成功: {template_name}")
            return True
        except Exception as e:
            logger.error(f"保存商品模板失败: {e}")
            return False
    
    def get_template(self, template_name: str) -> Optional[Dict]:
        """获取商品模板"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM product_templates WHERE template_name = ?
            ''', (template_name,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'template_name': row[1],
                    'title': row[2],
                    'description': row[3],
                    'price': row[4],
                    'category_id': row[5],
                    'images': json.loads(row[6]) if row[6] else [],
                    'tags': json.loads(row[7]) if row[7] else [],
                    'location': row[8],
                    'condition_type': row[9],
                    'trade_type': row[10],
                    'auto_publish': bool(row[11]),
                    'publish_schedule': json.loads(row[12]) if row[12] else {},
                    'created_time': row[13],
                    'updated_time': row[14]
                }
            return None
        except Exception as e:
            logger.error(f"获取商品模板失败: {e}")
            return None
    
    def list_templates(self) -> List[Dict]:
        """获取所有模板"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM product_templates ORDER BY updated_time DESC')
            rows = cursor.fetchall()
            conn.close()
            
            templates = []
            for row in rows:
                template = {
                    'id': row[0],
                    'template_name': row[1],
                    'title': row[2],
                    'price': row[4],
                    'auto_publish': bool(row[11]),
                    'created_time': row[13],
                    'updated_time': row[14]
                }
                templates.append(template)
            
            return templates
        except Exception as e:
            logger.error(f"获取模板列表失败: {e}")
            return []
    
    def upload_image(self, image_path: str) -> Optional[str]:
        """上传图片到闲鱼"""
        try:
            # 构造上传图片的API请求
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
                'api': 'mtop.taobao.idle.user.page.my.upload.image',
                'sessionOption': 'AutoLoginOnly',
            }
            
            # 读取图片文件
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            data_val = json.dumps({
                'image': image_data,
                'imageType': 'jpg'
            })
            
            data = {'data': data_val}
            
            # 生成签名
            token = self.xianyu_apis.session.cookies.get('_m_h5_tk', '').split('_')[0]
            sign = generate_sign(params['t'], token, data_val)
            params['sign'] = sign
            
            response = self.xianyu_apis.session.post(
                'https://h5api.m.goofish.com/h5/mtop.taobao.idle.user.page.my.upload.image/1.0/',
                params=params,
                data=data
            )
            
            result = response.json()
            if 'data' in result and 'imageUrl' in result['data']:
                logger.info(f"图片上传成功: {image_path}")
                return result['data']['imageUrl']
            else:
                logger.error(f"图片上传失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"图片上传异常: {e}")
            return None
    
    def publish_product(self, template_name: str, custom_data: Optional[Dict] = None) -> Optional[str]:
        """发布商品"""
        try:
            # 获取模板数据
            template = self.get_template(template_name)
            if not template:
                logger.error(f"未找到模板: {template_name}")
                return None
            
            # 合并自定义数据
            if custom_data:
                template.update(custom_data)
            
            # 构造发布商品的API请求
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
                'api': 'mtop.taobao.idle.user.publish',
                'sessionOption': 'AutoLoginOnly',
            }
            
            # 构造商品数据
            publish_data = {
                'title': template['title'],
                'desc': template['description'],
                'price': str(int(template['price'] * 100)),  # 价格转为分
                'categoryId': template['category_id'],
                'images': template['images'],
                'tags': template['tags'],
                'location': template['location'],
                'conditionType': template['condition_type'],
                'tradeType': template['trade_type'],
            }
            
            data_val = json.dumps(publish_data)
            data = {'data': data_val}
            
            # 生成签名
            token = self.xianyu_apis.session.cookies.get('_m_h5_tk', '').split('_')[0]
            sign = generate_sign(params['t'], token, data_val)
            params['sign'] = sign
            
            response = self.xianyu_apis.session.post(
                'https://h5api.m.goofish.com/h5/mtop.taobao.idle.user.publish/1.0/',
                params=params,
                data=data
            )
            
            result = response.json()
            
            # 检查发布结果
            if 'data' in result and 'itemId' in result['data']:
                item_id = result['data']['itemId']
                logger.info(f"商品发布成功: {template['title']} (ID: {item_id})")
                
                # 记录发布结果
                self._record_publish(template['id'], item_id, 'success')
                return item_id
            else:
                error_msg = str(result)
                logger.error(f"商品发布失败: {error_msg}")
                self._record_publish(template['id'], None, 'failed', error_msg)
                return None
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"商品发布异常: {error_msg}")
            if template:
                self._record_publish(template['id'], None, 'failed', error_msg)
            return None
    
    def _record_publish(self, template_id: int, item_id: Optional[str], 
                       status: str, error_message: Optional[str] = None):
        """记录发布结果"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO publish_records (template_id, item_id, status, error_message)
                VALUES (?, ?, ?, ?)
            ''', (template_id, item_id, status, error_message))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录发布结果失败: {e}")
    
    def get_publish_records(self, limit: int = 50) -> List[Dict]:
        """获取发布记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT pr.*, pt.template_name, pt.title 
                FROM publish_records pr
                LEFT JOIN product_templates pt ON pr.template_id = pt.id
                ORDER BY pr.publish_time DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            records = []
            for row in rows:
                record = {
                    'id': row[0],
                    'template_id': row[1],
                    'item_id': row[2],
                    'publish_time': row[3],
                    'status': row[4],
                    'error_message': row[5],
                    'template_name': row[6],
                    'title': row[7]
                }
                records.append(record)
            
            return records
        except Exception as e:
            logger.error(f"获取发布记录失败: {e}")
            return []
    
    def batch_publish(self, template_names: List[str], interval: int = 30) -> Dict[str, str]:
        """批量发布商品"""
        results = {}
        
        for i, template_name in enumerate(template_names):
            logger.info(f"正在发布第 {i+1}/{len(template_names)} 个商品: {template_name}")
            
            item_id = self.publish_product(template_name)
            results[template_name] = item_id or "发布失败"
            
            # 添加间隔，避免频繁请求
            if i < len(template_names) - 1:
                logger.info(f"等待 {interval} 秒后发布下一个商品...")
                time.sleep(interval)
        
        return results


# 使用示例和配置类
class ProductTemplateConfig:
    """商品模板配置类"""
    
    @staticmethod
    def create_digital_product_template() -> Dict:
        """创建数字产品模板"""
        return {
            'title': '数字产品激活码',
            'description': '正版激活码，自动发货，24小时在线客服',
            'price': 99.00,
            'category_id': '50022808',  # 软件类目ID
            'images': [],  # 图片URL列表
            'tags': ['数字产品', '激活码', '自动发货'],
            'location': '全国',
            'condition_type': 1,  # 全新
            'trade_type': 1,  # 邮寄
            'auto_publish': False,
            'publish_schedule': {
                'enabled': False,
                'time': '09:00',
                'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            }
        }
    
    @staticmethod
    def create_electronics_template() -> Dict:
        """创建电子产品模板"""
        return {
            'title': '电子产品名称',
            'description': '产品详细描述，包含规格、功能等信息',
            'price': 299.00,
            'category_id': '50025230',  # 电子产品类目ID
            'images': [],
            'tags': ['电子产品', '全新', '包邮'],
            'location': '北京',
            'condition_type': 1,
            'trade_type': 1,
            'auto_publish': False
        }