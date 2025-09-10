import os
import json
from datetime import datetime
from loguru import logger
from collections import defaultdict, deque

# 尝试导入sqlite3，如果失败则使用文件模式
try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    logger.warning("SQLite不可用，将使用文件模式存储数据")


class ChatContextManager:
    """
    聊天上下文管理器
    
    负责存储和检索用户与商品之间的对话历史，使用SQLite数据库进行持久化存储。
    支持按会话ID检索对话历史，以及议价次数统计。
    """
    
    def __init__(self, max_history=100, db_path="data/chat_history.db", force_file_mode=False):
        """
        初始化聊天上下文管理器
        
        Args:
            max_history: 每个对话保留的最大消息数
            db_path: SQLite数据库文件路径或数据目录路径
            force_file_mode: 强制使用文件模式
        """
        self.max_history = max_history
        self.db_path = db_path
        
        # 自动选择存储模式
        self.use_file_mode = force_file_mode or not SQLITE_AVAILABLE
        
        if self.use_file_mode:
            logger.info("使用文件模式存储数据")
            self._init_file_storage()
        else:
            logger.info("使用SQLite数据库存储数据")
            self._init_db()
        
    def _init_db(self):
        """初始化数据库表结构"""
        # 确保数据库目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建消息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            chat_id TEXT
        )
        ''')
        
        # 检查是否需要添加chat_id字段（兼容旧数据库）
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'chat_id' not in columns:
            cursor.execute('ALTER TABLE messages ADD COLUMN chat_id TEXT')
            logger.info("已为messages表添加chat_id字段")
        
        # 创建索引以加速查询
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_item ON messages (user_id, item_id)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chat_id ON messages (chat_id)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON messages (timestamp)
        ''')
        
        # 创建基于会话ID的议价次数表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_bargain_counts (
            chat_id TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建商品信息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            price REAL,
            description TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"聊天历史数据库初始化完成: {self.db_path}")

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
        
        # 内存存储结构
        self.chat_messages = defaultdict(lambda: deque(maxlen=self.max_history))
        self.bargain_counts = defaultdict(int)
        self.item_cache = {}
        
        # 数据文件路径
        self.messages_file = os.path.join(self.data_dir, "chat_messages.json")
        self.bargain_file = os.path.join(self.data_dir, "bargain_counts.json") 
        self.items_file = os.path.join(self.data_dir, "item_cache.json")
        
        # 加载现有数据
        self._load_file_data()
        logger.info(f"文件存储模式初始化完成: {self.data_dir}")

    def _load_file_data(self):
        """从文件加载数据到内存"""
        try:
            # 加载对话历史
            if os.path.exists(self.messages_file):
                with open(self.messages_file, 'r', encoding='utf-8') as f:
                    messages_data = json.load(f)
                    for chat_id, messages in messages_data.items():
                        self.chat_messages[chat_id] = deque(messages, maxlen=self.max_history)
                logger.info(f"加载对话历史: {len(messages_data)} 个会话")
            
            # 加载议价统计
            if os.path.exists(self.bargain_file):
                with open(self.bargain_file, 'r', encoding='utf-8') as f:
                    self.bargain_counts.update(json.load(f))
                logger.info(f"加载议价统计: {len(self.bargain_counts)} 个会话")
            
            # 加载商品缓存
            if os.path.exists(self.items_file):
                with open(self.items_file, 'r', encoding='utf-8') as f:
                    self.item_cache.update(json.load(f))
                logger.info(f"加载商品缓存: {len(self.item_cache)} 个商品")
                
        except Exception as e:
            logger.warning(f"加载数据文件失败: {e}")

    def _save_file_data(self, data_type='all'):
        """保存数据到文件"""
        try:
            if data_type in ['all', 'messages']:
                # 保存对话历史
                messages_data = {}
                for chat_id, messages in self.chat_messages.items():
                    messages_data[chat_id] = list(messages)
                
                with open(self.messages_file, 'w', encoding='utf-8') as f:
                    json.dump(messages_data, f, ensure_ascii=False, indent=2)
            
            if data_type in ['all', 'bargain']:
                # 保存议价统计
                with open(self.bargain_file, 'w', encoding='utf-8') as f:
                    json.dump(dict(self.bargain_counts), f, ensure_ascii=False, indent=2)
            
            if data_type in ['all', 'items']:
                # 保存商品缓存
                with open(self.items_file, 'w', encoding='utf-8') as f:
                    json.dump(self.item_cache, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logger.error(f"保存数据文件失败: {e}")
        
    def get_all_conversations(self, limit=50):
        """
        获取所有会话列表
        
        Args:
            limit: 返回的会话数量限制
            
        Returns:
            list: 会话列表
        """
        if self.use_file_mode:
            return self._get_all_conversations_file_mode(limit)
        else:
            return self._get_all_conversations_db_mode(limit)
    
    def _get_all_conversations_file_mode(self, limit=50):
        """文件模式：获取所有会话列表"""
        try:
            conversations = []
            
            for chat_id, messages in self.chat_messages.items():
                if not messages:
                    continue
                    
                # 获取最后一条消息的信息
                last_message = messages[-1]
                first_message = messages[0]
                
                conversations.append({
                    'chat_id': chat_id,
                    'user_id': first_message.get('user_id', ''),
                    'item_id': first_message.get('item_id', ''),
                    'last_message_time': last_message.get('timestamp', ''),
                    'message_count': len(messages)
                })
            
            # 按最后消息时间排序
            conversations.sort(key=lambda x: x['last_message_time'], reverse=True)
            
            return conversations[:limit]
        except Exception as e:
            logger.error(f"获取会话列表时出错: {e}")
            return []
    
    def _get_all_conversations_db_mode(self, limit=50):
        """数据库模式：获取所有会话列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    chat_id,
                    user_id,
                    item_id,
                    MAX(timestamp) as last_message_time,
                    COUNT(*) as message_count
                FROM messages 
                WHERE chat_id IS NOT NULL
                GROUP BY chat_id 
                ORDER BY last_message_time DESC 
                LIMIT ?
            """, (limit,))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    'chat_id': row[0],
                    'user_id': row[1],
                    'item_id': row[2],
                    'last_message_time': row[3],
                    'message_count': row[4]
                })
            
            return conversations
        except Exception as e:
            logger.error(f"获取会话列表时出错: {e}")
            return []
        finally:
            conn.close()
    
    def get_conversation_detail(self, chat_id):
        """
        获取会话详情
        
        Args:
            chat_id: 会话ID
            
        Returns:
            dict: 会话详情
        """
        if self.use_file_mode:
            return self._get_conversation_detail_file_mode(chat_id)
        else:
            return self._get_conversation_detail_db_mode(chat_id)
    
    def _get_conversation_detail_file_mode(self, chat_id):
        """文件模式：获取会话详情"""
        try:
            messages = self.chat_messages.get(chat_id, [])
            if not messages:
                return None
            
            first_message = messages[0]
            last_message = messages[-1]
            
            # 获取议价次数
            bargain_count = self.bargain_counts.get(chat_id, 0)
            
            # 获取商品信息
            item_id = first_message.get('item_id')
            item_info = self.get_item_info(item_id) if item_id else None
            
            return {
                'chat_id': chat_id,
                'user_id': first_message.get('user_id', ''),
                'item_id': item_id or '',
                'first_message_time': first_message.get('timestamp', ''),
                'last_message_time': last_message.get('timestamp', ''),
                'total_messages': len(messages),
                'bargain_count': bargain_count,
                'item_info': item_info
            }
        except Exception as e:
            logger.error(f"获取会话详情时出错: {e}")
            return None
    
    def _get_conversation_detail_db_mode(self, chat_id):
        """数据库模式：获取会话详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取会话基本信息
            cursor.execute("""
                SELECT 
                    user_id,
                    item_id,
                    MIN(timestamp) as first_message_time,
                    MAX(timestamp) as last_message_time,
                    COUNT(*) as total_messages
                FROM messages 
                WHERE chat_id = ?
            """, (chat_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # 获取议价次数
            bargain_count = self.get_bargain_count_by_chat(chat_id)
            
            # 获取商品信息
            item_info = self.get_item_info(row[1]) if row[1] else None
            
            return {
                'chat_id': chat_id,
                'user_id': row[0],
                'item_id': row[1],
                'first_message_time': row[2],
                'last_message_time': row[3],
                'total_messages': row[4],
                'bargain_count': bargain_count,
                'item_info': item_info
            }
        except Exception as e:
            logger.error(f"获取会话详情时出错: {e}")
            return None
        finally:
            conn.close()
    
    def get_stats(self):
        """
        获取统计信息
        
        Returns:
            dict: 包含数据统计的字典
        """
        if self.use_file_mode:
            return self._get_stats_file_mode()
        else:
            return self._get_stats_db_mode()
    
    def _get_stats_file_mode(self):
        """文件模式：获取统计信息"""
        total_conversations = len(self.chat_messages)
        total_messages = sum(len(messages) for messages in self.chat_messages.values())
        cached_items = len(self.item_cache)
        active_bargains = len([count for count in self.bargain_counts.values() if count > 0])
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'cached_items': cached_items,
            'active_bargains': active_bargains
        }
    
    def _get_stats_db_mode(self):
        """数据库模式：获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取会话数
            cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM messages WHERE chat_id IS NOT NULL")
            total_conversations = cursor.fetchone()[0]
            
            # 获取消息数
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            # 获取商品数
            cursor.execute("SELECT COUNT(*) FROM items")
            cached_items = cursor.fetchone()[0]
            
            # 获取活跃议价数
            cursor.execute("SELECT COUNT(*) FROM chat_bargain_counts WHERE count > 0")
            active_bargains = cursor.fetchone()[0]
            
            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'cached_items': cached_items,
                'active_bargains': active_bargains
            }
        except Exception as e:
            logger.error(f"获取统计信息时出错: {e}")
            return {
                'total_conversations': 0,
                'total_messages': 0,
                'cached_items': 0,
                'active_bargains': 0
            }
        finally:
            conn.close()
            
    def save_item_info(self, item_id, item_data):
        """
        保存商品信息到数据库
        
        Args:
            item_id: 商品ID
            item_data: 商品信息字典
        """
        if self.use_file_mode:
            # 简化商品信息，只保存关键字段
            simplified_item = {
                "desc": item_data.get("desc", ""),
                "soldPrice": item_data.get("soldPrice", 0),
                "title": item_data.get("title", ""),
                "cached_time": datetime.now().isoformat()
            }
            
            self.item_cache[item_id] = simplified_item
            logger.debug(f"缓存商品信息: {item_id}")
            self._save_file_data('items')
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 从商品数据中提取有用信息
                price = float(item_data.get('soldPrice', 0))
                description = item_data.get('desc', '')
                
                # 将整个商品数据转换为JSON字符串
                data_json = json.dumps(item_data, ensure_ascii=False)
                
                cursor.execute(
                    """
                    INSERT INTO items (item_id, data, price, description, last_updated) 
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(item_id) 
                    DO UPDATE SET data = ?, price = ?, description = ?, last_updated = ?
                    """,
                    (
                        item_id, data_json, price, description, datetime.now().isoformat(),
                        data_json, price, description, datetime.now().isoformat()
                    )
                )
                
                conn.commit()
                logger.debug(f"商品信息已保存: {item_id}")
            except Exception as e:
                logger.error(f"保存商品信息时出错: {e}")
                conn.rollback()
            finally:
                conn.close()
    
    def get_item_info(self, item_id):
        """
        从数据库获取商品信息
        
        Args:
            item_id: 商品ID
            
        Returns:
            dict: 商品信息字典，如果不存在返回None
        """
        if self.use_file_mode:
            return self.item_cache.get(item_id)
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "SELECT data FROM items WHERE item_id = ?",
                    (item_id,)
                )
                
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return None
            except Exception as e:
                logger.error(f"获取商品信息时出错: {e}")
                return None
            finally:
                conn.close()

    def add_message_by_chat(self, chat_id, user_id, item_id, role, content):
        """
        基于会话ID添加新消息到对话历史
        
        Args:
            chat_id: 会话ID
            user_id: 用户ID (用户消息存真实user_id，助手消息存卖家ID)
            item_id: 商品ID
            role: 消息角色 (user/assistant)
            content: 消息内容
        """
        if self.use_file_mode:
            self._add_message_file_mode(chat_id, user_id, item_id, role, content)
        else:
            self._add_message_db_mode(chat_id, user_id, item_id, role, content)

    def _add_message_file_mode(self, chat_id, user_id, item_id, role, content):
        """文件模式：添加消息"""
        message = {
            "user_id": user_id,
            "item_id": item_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.chat_messages[chat_id].append(message)
        self._save_file_data('messages')

    def _add_message_db_mode(self, chat_id, user_id, item_id, role, content):
        """数据库模式：添加消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO messages (user_id, item_id, role, content, timestamp, chat_id) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, item_id, role, content, datetime.now().isoformat(), chat_id)
            )
            
            cursor.execute(
                """
                SELECT id FROM messages 
                WHERE chat_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?, 1
                """, 
                (chat_id, self.max_history)
            )
            
            oldest_to_keep = cursor.fetchone()
            if oldest_to_keep:
                cursor.execute(
                    "DELETE FROM messages WHERE chat_id = ? AND id < ?",
                    (chat_id, oldest_to_keep[0])
                )
            
            conn.commit()
        except Exception as e:
            logger.error(f"添加消息到数据库时出错: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_context_by_chat(self, chat_id):
        """
        基于会话ID获取对话历史
        
        Args:
            chat_id: 会话ID
            
        Returns:
            list: 包含对话历史的列表
        """
        if self.use_file_mode:
            return self._get_context_file_mode(chat_id)
        else:
            return self._get_context_db_mode(chat_id)

    def _get_context_file_mode(self, chat_id):
        """文件模式：获取对话历史"""
        messages = []
        
        # 从内存获取消息
        for msg in self.chat_messages[chat_id]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # 添加议价次数信息
        bargain_count = self.bargain_counts.get(chat_id, 0)
        if bargain_count > 0:
            messages.append({
                "role": "system",
                "content": f"议价次数: {bargain_count}"
            })
        
        return messages

    def _get_context_db_mode(self, chat_id):
        """数据库模式：获取对话历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                SELECT role, content FROM messages 
                WHERE chat_id = ? 
                ORDER BY timestamp ASC
                LIMIT ?
                """, 
                (chat_id, self.max_history)
            )
            
            messages = [{"role": role, "content": content} for role, content in cursor.fetchall()]
            
            # 获取议价次数并添加到上下文中
            bargain_count = self.get_bargain_count_by_chat(chat_id)
            if bargain_count > 0:
                messages.append({
                    "role": "system", 
                    "content": f"议价次数: {bargain_count}"
                })
            
        except Exception as e:
            logger.error(f"获取对话历史时出错: {e}")
            messages = []
        finally:
            conn.close()
        
        return messages

    def increment_bargain_count_by_chat(self, chat_id):
        """
        基于会话ID增加议价次数
        
        Args:
            chat_id: 会话ID
        """
        if self.use_file_mode:
            self.bargain_counts[chat_id] += 1
            logger.debug(f"会话 {chat_id} 议价次数: {self.bargain_counts[chat_id]}")
            self._save_file_data('bargain')
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    """
                    INSERT INTO chat_bargain_counts (chat_id, count, last_updated)
                    VALUES (?, 1, ?)
                    ON CONFLICT(chat_id) 
                    DO UPDATE SET count = count + 1, last_updated = ?
                    """,
                    (chat_id, datetime.now().isoformat(), datetime.now().isoformat())
                )
                
                conn.commit()
                logger.debug(f"会话 {chat_id} 议价次数已增加")
            except Exception as e:
                logger.error(f"增加议价次数时出错: {e}")
                conn.rollback()
            finally:
                conn.close()

    def get_bargain_count_by_chat(self, chat_id):
        """
        基于会话ID获取议价次数
        
        Args:
            chat_id: 会话ID
            
        Returns:
            int: 议价次数
        """
        if self.use_file_mode:
            return self.bargain_counts.get(chat_id, 0)
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "SELECT count FROM chat_bargain_counts WHERE chat_id = ?",
                    (chat_id,)
                )
                
                result = cursor.fetchone()
                return result[0] if result else 0
            except Exception as e:
                logger.error(f"获取议价次数时出错: {e}")
                return 0
            finally:
                conn.close() 