# -*- coding: utf-8 -*-
"""
自动发货管理器
支持虚拟商品自动发货功能
"""

import os
import json
from datetime import datetime
from loguru import logger
from typing import Dict, List, Optional

# 尝试导入sqlite3
try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    logger.warning("SQLite不可用，将使用文件模式存储数据")


class DeliveryManager:
    """
    自动发货管理器

    负责管理商品发货配置和发货记录
    支持网盘链接、卡密、自定义文本等多种发货方式
    """

    def __init__(self, db_path="data/delivery.db", force_file_mode=False):
        """
        初始化发货管理器

        Args:
            db_path: SQLite数据库文件路径或数据目录路径
            force_file_mode: 强制使用文件模式
        """
        self.db_path = db_path

        # 自动选择存储模式
        self.use_file_mode = force_file_mode or not SQLITE_AVAILABLE

        if self.use_file_mode:
            logger.info("发货管理器使用文件模式存储数据")
            self._init_file_storage()
        else:
            logger.info("发货管理器使用SQLite数据库存储数据")
            self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        # 确保数据库目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建商品发货配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS delivery_configs (
            item_id TEXT PRIMARY KEY,
            delivery_type TEXT NOT NULL,
            delivery_content TEXT NOT NULL,
            extraction_code TEXT,
            custom_message TEXT,
            is_enabled INTEGER DEFAULT 1,
            stock_count INTEGER DEFAULT -1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建发货记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS delivery_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            item_id TEXT NOT NULL,
            buyer_id TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            delivery_type TEXT NOT NULL,
            delivery_content TEXT NOT NULL,
            delivery_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'success',
            error_message TEXT
        )
        ''')

        # 创建索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_delivery_item_id ON delivery_configs (item_id)
        ''')

        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_delivery_records_item ON delivery_records (item_id)
        ''')

        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_delivery_records_buyer ON delivery_records (buyer_id)
        ''')

        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_delivery_records_time ON delivery_records (delivery_time)
        ''')

        conn.commit()
        conn.close()
        logger.info(f"发货数据库初始化完成: {self.db_path}")

    def _init_file_storage(self):
        """初始化文件存储模式"""
        # 确定数据目录
        if self.db_path.endswith('.db'):
            self.data_dir = os.path.dirname(self.db_path) or "data"
        else:
            self.data_dir = self.db_path

        # 创建数据目录
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # 数据文件路径
        self.configs_file = os.path.join(self.data_dir, "delivery_configs.json")
        self.records_file = os.path.join(self.data_dir, "delivery_records.json")

        # 内存存储结构
        self.configs = {}
        self.records = []

        # 加载现有数据
        self._load_file_data()
        logger.info(f"发货文件存储模式初始化完成: {self.data_dir}")

    def _load_file_data(self):
        """从文件加载数据到内存"""
        try:
            # 加载发货配置
            if os.path.exists(self.configs_file):
                with open(self.configs_file, 'r', encoding='utf-8') as f:
                    self.configs = json.load(f)
                logger.info(f"加载发货配置: {len(self.configs)} 个商品")

            # 加载发货记录
            if os.path.exists(self.records_file):
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
                logger.info(f"加载发货记录: {len(self.records)} 条")

        except Exception as e:
            logger.warning(f"加载数据文件失败: {e}")

    def _save_file_data(self, data_type='all'):
        """保存数据到文件"""
        try:
            if data_type in ['all', 'configs']:
                with open(self.configs_file, 'w', encoding='utf-8') as f:
                    json.dump(self.configs, f, ensure_ascii=False, indent=2)

            if data_type in ['all', 'records']:
                with open(self.records_file, 'w', encoding='utf-8') as f:
                    json.dump(self.records, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存数据文件失败: {e}")

    # ========== 发货配置管理 ==========

    def save_delivery_config(self, item_id: str, config: Dict) -> bool:
        """
        保存商品发货配置

        Args:
            item_id: 商品ID
            config: 发货配置字典
                - delivery_type: 发货类型 (netdisk/cardkey/text)
                - delivery_content: 发货内容（网盘链接/卡密/文本）
                - extraction_code: 提取码（可选）
                - custom_message: 自定义消息模板（可选）
                - is_enabled: 是否启用自动发货（默认True）
                - stock_count: 库存数量（默认-1表示无限）

        Returns:
            bool: 是否成功
        """
        if self.use_file_mode:
            return self._save_config_file_mode(item_id, config)
        else:
            return self._save_config_db_mode(item_id, config)

    def _save_config_file_mode(self, item_id: str, config: Dict) -> bool:
        """文件模式：保存发货配置"""
        try:
            self.configs[item_id] = {
                'item_id': item_id,
                'delivery_type': config.get('delivery_type', 'netdisk'),
                'delivery_content': config.get('delivery_content', ''),
                'extraction_code': config.get('extraction_code', ''),
                'custom_message': config.get('custom_message', ''),
                'is_enabled': config.get('is_enabled', True),
                'stock_count': config.get('stock_count', -1),
                'updated_at': datetime.now().isoformat()
            }

            # 添加创建时间（仅首次）
            if 'created_at' not in self.configs[item_id]:
                self.configs[item_id]['created_at'] = datetime.now().isoformat()

            self._save_file_data('configs')
            logger.info(f"发货配置已保存: {item_id}")
            return True

        except Exception as e:
            logger.error(f"保存发货配置失败: {e}")
            return False

    def _save_config_db_mode(self, item_id: str, config: Dict) -> bool:
        """数据库模式：保存发货配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO delivery_configs
                (item_id, delivery_type, delivery_content, extraction_code,
                 custom_message, is_enabled, stock_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id)
                DO UPDATE SET
                    delivery_type = ?,
                    delivery_content = ?,
                    extraction_code = ?,
                    custom_message = ?,
                    is_enabled = ?,
                    stock_count = ?,
                    updated_at = ?
                """,
                (
                    item_id,
                    config.get('delivery_type', 'netdisk'),
                    config.get('delivery_content', ''),
                    config.get('extraction_code', ''),
                    config.get('custom_message', ''),
                    1 if config.get('is_enabled', True) else 0,
                    config.get('stock_count', -1),
                    datetime.now().isoformat(),
                    # UPDATE部分
                    config.get('delivery_type', 'netdisk'),
                    config.get('delivery_content', ''),
                    config.get('extraction_code', ''),
                    config.get('custom_message', ''),
                    1 if config.get('is_enabled', True) else 0,
                    config.get('stock_count', -1),
                    datetime.now().isoformat()
                )
            )

            conn.commit()
            logger.info(f"发货配置已保存: {item_id}")
            return True

        except Exception as e:
            logger.error(f"保存发货配置失败: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def get_delivery_config(self, item_id: str) -> Optional[Dict]:
        """
        获取商品发货配置

        Args:
            item_id: 商品ID

        Returns:
            dict: 发货配置，如果不存在返回None
        """
        if self.use_file_mode:
            return self._get_config_file_mode(item_id)
        else:
            return self._get_config_db_mode(item_id)

    def _get_config_file_mode(self, item_id: str) -> Optional[Dict]:
        """文件模式：获取发货配置"""
        return self.configs.get(item_id)

    def _get_config_db_mode(self, item_id: str) -> Optional[Dict]:
        """数据库模式：获取发货配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT item_id, delivery_type, delivery_content, extraction_code,
                       custom_message, is_enabled, stock_count, created_at, updated_at
                FROM delivery_configs
                WHERE item_id = ?
                """,
                (item_id,)
            )

            row = cursor.fetchone()
            if row:
                return {
                    'item_id': row[0],
                    'delivery_type': row[1],
                    'delivery_content': row[2],
                    'extraction_code': row[3],
                    'custom_message': row[4],
                    'is_enabled': bool(row[5]),
                    'stock_count': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                }
            return None

        except Exception as e:
            logger.error(f"获取发货配置失败: {e}")
            return None

        finally:
            conn.close()

    def delete_delivery_config(self, item_id: str) -> bool:
        """
        删除商品发货配置

        Args:
            item_id: 商品ID

        Returns:
            bool: 是否成功
        """
        if self.use_file_mode:
            if item_id in self.configs:
                del self.configs[item_id]
                self._save_file_data('configs')
                logger.info(f"发货配置已删除: {item_id}")
                return True
            return False
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("DELETE FROM delivery_configs WHERE item_id = ?", (item_id,))
                conn.commit()
                logger.info(f"发货配置已删除: {item_id}")
                return True

            except Exception as e:
                logger.error(f"删除发货配置失败: {e}")
                conn.rollback()
                return False

            finally:
                conn.close()

    def list_delivery_configs(self, enabled_only: bool = False) -> List[Dict]:
        """
        获取所有发货配置列表

        Args:
            enabled_only: 是否只返回已启用的配置

        Returns:
            list: 发货配置列表
        """
        if self.use_file_mode:
            configs = list(self.configs.values())
            if enabled_only:
                configs = [c for c in configs if c.get('is_enabled', False)]
            return configs
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                query = """
                    SELECT item_id, delivery_type, delivery_content, extraction_code,
                           custom_message, is_enabled, stock_count, created_at, updated_at
                    FROM delivery_configs
                """
                if enabled_only:
                    query += " WHERE is_enabled = 1"

                cursor.execute(query)

                configs = []
                for row in cursor.fetchall():
                    configs.append({
                        'item_id': row[0],
                        'delivery_type': row[1],
                        'delivery_content': row[2],
                        'extraction_code': row[3],
                        'custom_message': row[4],
                        'is_enabled': bool(row[5]),
                        'stock_count': row[6],
                        'created_at': row[7],
                        'updated_at': row[8]
                    })

                return configs

            except Exception as e:
                logger.error(f"获取发货配置列表失败: {e}")
                return []

            finally:
                conn.close()

    # ========== 发货记录管理 ==========

    def record_delivery(self, record: Dict) -> bool:
        """
        记录发货信息

        Args:
            record: 发货记录字典
                - order_id: 订单ID（可选）
                - item_id: 商品ID
                - buyer_id: 买家ID
                - chat_id: 会话ID
                - delivery_type: 发货类型
                - delivery_content: 发货内容
                - status: 状态 (success/failed)
                - error_message: 错误信息（可选）

        Returns:
            bool: 是否成功
        """
        if self.use_file_mode:
            return self._record_delivery_file_mode(record)
        else:
            return self._record_delivery_db_mode(record)

    def _record_delivery_file_mode(self, record: Dict) -> bool:
        """文件模式：记录发货"""
        try:
            delivery_record = {
                'id': len(self.records) + 1,
                'order_id': record.get('order_id', ''),
                'item_id': record.get('item_id', ''),
                'buyer_id': record.get('buyer_id', ''),
                'chat_id': record.get('chat_id', ''),
                'delivery_type': record.get('delivery_type', ''),
                'delivery_content': record.get('delivery_content', ''),
                'delivery_time': datetime.now().isoformat(),
                'status': record.get('status', 'success'),
                'error_message': record.get('error_message', '')
            }

            self.records.append(delivery_record)
            self._save_file_data('records')
            logger.info(f"发货记录已保存: 商品{record.get('item_id')}, 买家{record.get('buyer_id')}")
            return True

        except Exception as e:
            logger.error(f"保存发货记录失败: {e}")
            return False

    def _record_delivery_db_mode(self, record: Dict) -> bool:
        """数据库模式：记录发货"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO delivery_records
                (order_id, item_id, buyer_id, chat_id, delivery_type,
                 delivery_content, delivery_time, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get('order_id', ''),
                    record.get('item_id', ''),
                    record.get('buyer_id', ''),
                    record.get('chat_id', ''),
                    record.get('delivery_type', ''),
                    record.get('delivery_content', ''),
                    datetime.now().isoformat(),
                    record.get('status', 'success'),
                    record.get('error_message', '')
                )
            )

            conn.commit()
            logger.info(f"发货记录已保存: 商品{record.get('item_id')}, 买家{record.get('buyer_id')}")
            return True

        except Exception as e:
            logger.error(f"保存发货记录失败: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def get_delivery_records(self, item_id: str = None, buyer_id: str = None,
                            limit: int = 100) -> List[Dict]:
        """
        获取发货记录

        Args:
            item_id: 商品ID（可选）
            buyer_id: 买家ID（可选）
            limit: 返回记录数量限制

        Returns:
            list: 发货记录列表
        """
        if self.use_file_mode:
            return self._get_records_file_mode(item_id, buyer_id, limit)
        else:
            return self._get_records_db_mode(item_id, buyer_id, limit)

    def _get_records_file_mode(self, item_id: str, buyer_id: str, limit: int) -> List[Dict]:
        """文件模式：获取发货记录"""
        records = self.records.copy()

        # 筛选
        if item_id:
            records = [r for r in records if r.get('item_id') == item_id]
        if buyer_id:
            records = [r for r in records if r.get('buyer_id') == buyer_id]

        # 按时间倒序排序
        records.sort(key=lambda x: x.get('delivery_time', ''), reverse=True)

        return records[:limit]

    def _get_records_db_mode(self, item_id: str, buyer_id: str, limit: int) -> List[Dict]:
        """数据库模式：获取发货记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, order_id, item_id, buyer_id, chat_id, delivery_type,
                       delivery_content, delivery_time, status, error_message
                FROM delivery_records
                WHERE 1=1
            """
            params = []

            if item_id:
                query += " AND item_id = ?"
                params.append(item_id)

            if buyer_id:
                query += " AND buyer_id = ?"
                params.append(buyer_id)

            query += " ORDER BY delivery_time DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            records = []
            for row in cursor.fetchall():
                records.append({
                    'id': row[0],
                    'order_id': row[1],
                    'item_id': row[2],
                    'buyer_id': row[3],
                    'chat_id': row[4],
                    'delivery_type': row[5],
                    'delivery_content': row[6],
                    'delivery_time': row[7],
                    'status': row[8],
                    'error_message': row[9]
                })

            return records

        except Exception as e:
            logger.error(f"获取发货记录失败: {e}")
            return []

        finally:
            conn.close()

    def get_delivery_stats(self) -> Dict:
        """
        获取发货统计信息

        Returns:
            dict: 统计信息
        """
        if self.use_file_mode:
            total_configs = len(self.configs)
            enabled_configs = len([c for c in self.configs.values() if c.get('is_enabled', False)])
            total_deliveries = len(self.records)
            success_deliveries = len([r for r in self.records if r.get('status') == 'success'])
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT COUNT(*) FROM delivery_configs")
                total_configs = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM delivery_configs WHERE is_enabled = 1")
                enabled_configs = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM delivery_records")
                total_deliveries = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM delivery_records WHERE status = 'success'")
                success_deliveries = cursor.fetchone()[0]

            except Exception as e:
                logger.error(f"获取统计信息失败: {e}")
                return {}

            finally:
                conn.close()

        return {
            'total_configs': total_configs,
            'enabled_configs': enabled_configs,
            'total_deliveries': total_deliveries,
            'success_deliveries': success_deliveries,
            'success_rate': round(success_deliveries / total_deliveries * 100, 2) if total_deliveries > 0 else 0
        }

    # ========== 发货消息生成 ==========

    def build_delivery_message(self, config: Dict, item_info: Dict = None) -> str:
        """
        构建发货消息

        Args:
            config: 发货配置
            item_info: 商品信息（可选）

        Returns:
            str: 发货消息文本
        """
        delivery_type = config.get('delivery_type', 'netdisk')

        # 如果有自定义消息模板，使用模板
        if config.get('custom_message'):
            message = config['custom_message']
            # 替换变量
            message = message.replace('{content}', config.get('delivery_content', ''))
            message = message.replace('{code}', config.get('extraction_code', ''))
            if item_info:
                message = message.replace('{title}', item_info.get('title', ''))
                message = message.replace('{price}', str(item_info.get('soldPrice', '')))
            return message

        # 默认消息模板
        if delivery_type == 'netdisk':
            message = f"您好！感谢购买，以下是商品资源：\n\n"
            message += f"📦 网盘链接：{config.get('delivery_content', '')}\n"
            if config.get('extraction_code'):
                message += f"🔑 提取码：{config.get('extraction_code')}\n"
            message += f"\n请及时保存，如有问题请随时联系我。祝您使用愉快！"

        elif delivery_type == 'cardkey':
            message = f"您好！感谢购买，以下是您的卡密信息：\n\n"
            message += f"🎟️ 卡密：{config.get('delivery_content', '')}\n"
            message += f"\n请妥善保管，如有问题请随时联系我。"

        elif delivery_type == 'text':
            message = config.get('delivery_content', '')

        else:
            message = config.get('delivery_content', '')

        return message

    def check_stock(self, item_id: str) -> bool:
        """
        检查库存是否充足

        Args:
            item_id: 商品ID

        Returns:
            bool: 是否有库存
        """
        config = self.get_delivery_config(item_id)
        if not config:
            return False

        stock_count = config.get('stock_count', -1)

        # -1表示无限库存
        if stock_count == -1:
            return True

        # 检查库存是否大于0
        return stock_count > 0

    def decrease_stock(self, item_id: str, count: int = 1) -> bool:
        """
        减少库存

        Args:
            item_id: 商品ID
            count: 减少数量

        Returns:
            bool: 是否成功
        """
        config = self.get_delivery_config(item_id)
        if not config:
            return False

        stock_count = config.get('stock_count', -1)

        # -1表示无限库存，不需要减少
        if stock_count == -1:
            return True

        # 检查库存是否充足
        if stock_count < count:
            logger.warning(f"商品{item_id}库存不足: 当前{stock_count}, 需要{count}")
            return False

        # 更新库存
        config['stock_count'] = stock_count - count
        return self.save_delivery_config(item_id, config)
