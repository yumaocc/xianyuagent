# 🏪 闲鱼店铺自动化管理系统设计文档

## 📋 项目概述

基于现有闲鱼智能客服系统，扩展订单自动化处理功能，实现从用户咨询到自动发货的完整闭环管理。

### 🎯 核心需求
1. **智能客服** - 自动回复消息，促成交易（✅ 已实现）
2. **商品管理** - 后台配置商品自动发货规则
3. **订单监听** - 实时检测用户付款状态
4. **自动发货** - 虚拟商品/配置商品自动发货
5. **手动提醒** - 需人工发货的商品通知提醒
6. **数据统计** - 交易数据和发货统计

---

## 🏗️ 系统整体架构

```
闲鱼WebSocket监听 → 消息处理中心 → 智能客服系统
                            ↓
                    订单状态监听
                            ↓
                    订单管理器
                   ↙         ↘
        自动发货系统    通知提醒系统
         ↓                ↓
    发货API调用      微信/短信通知
                            
Web管理后台 ← 商品配置管理 ← 订单状态数据库
```

### 核心组件
- **消息处理中心**: 扩展现有WebSocket消息处理
- **订单管理器**: 订单状态机管理和业务逻辑
- **自动发货系统**: 根据配置自动执行发货操作
- **通知提醒系统**: 微信机器人/短信/邮件通知
- **Web管理后台**: 商品配置和数据统计界面
- **数据存储**: 订单数据库和商品配置数据库

---

## 📦 商品配置系统设计

### 数据库设计

```sql
-- 商品配置表
CREATE TABLE product_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT UNIQUE NOT NULL,           -- 商品ID
    title TEXT NOT NULL,                    -- 商品标题
    category TEXT DEFAULT 'physical',       -- 商品类型: virtual/physical
    auto_ship BOOLEAN DEFAULT FALSE,        -- 是否自动发货
    ship_delay_min INTEGER DEFAULT 5,       -- 发货延时最小值(分钟)
    ship_delay_max INTEGER DEFAULT 30,      -- 发货延时最大值(分钟)
    logistics_company TEXT DEFAULT '顺丰快递', -- 默认物流公司
    ship_template TEXT,                     -- 发货模板内容(虚拟商品)
    stock_quantity INTEGER DEFAULT -1,      -- 库存数量(-1表示无限)
    status TEXT DEFAULT 'active',           -- 商品状态: active/inactive/out_of_stock
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 商品库存记录表
CREATE TABLE product_stock_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    action TEXT NOT NULL,                   -- 操作类型: sold/restock/adjust
    quantity_change INTEGER,                -- 数量变化
    remaining_stock INTEGER,                -- 剩余库存
    order_id TEXT,                         -- 关联订单ID
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 配置管理接口

```python
class ProductConfigManager:
    """商品配置管理器"""
    
    def add_product_config(self, item_id: str, config: dict) -> bool:
        """添加商品配置"""
        
    def update_product_config(self, item_id: str, config: dict) -> bool:
        """更新商品配置"""
        
    def get_product_config(self, item_id: str) -> dict:
        """获取商品配置"""
        
    def delete_product_config(self, item_id: str) -> bool:
        """删除商品配置"""
        
    def list_product_configs(self, status='active') -> list:
        """获取商品配置列表"""
        
    def is_auto_ship_enabled(self, item_id: str) -> bool:
        """检查商品是否启用自动发货"""
        
    def update_stock(self, item_id: str, quantity_change: int, order_id: str = None) -> bool:
        """更新商品库存"""
```

---

## 📊 订单监听系统设计

### 订单状态机

```python
class OrderStatus(Enum):
    PENDING_PAYMENT = "等待买家付款"      # 买家未付款
    PENDING_SHIP = "等待卖家发货"        # 买家已付款，等待发货  
    SHIPPED = "已发货"                  # 卖家已发货
    COMPLETED = "交易成功"              # 买家确认收货
    CANCELLED = "交易关闭"              # 交易取消/关闭
    REFUNDING = "退款中"                # 退款处理中
    
状态转换规则:
PENDING_PAYMENT → PENDING_SHIP  (用户付款)
PENDING_PAYMENT → CANCELLED     (订单取消)
PENDING_SHIP → SHIPPED         (自动发货)
SHIPPED → COMPLETED            (用户确认收货)
任意状态 → REFUNDING            (发起退款)
```

### 订单数据库设计

```sql
-- 订单管理表
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,          -- 订单ID
    chat_id TEXT NOT NULL,                  -- 会话ID
    user_id TEXT NOT NULL,                  -- 买家用户ID
    item_id TEXT NOT NULL,                  -- 商品ID
    item_title TEXT,                        -- 商品标题
    amount REAL,                           -- 交易金额
    status TEXT NOT NULL,                   -- 订单状态
    payment_time DATETIME,                  -- 付款时间
    ship_time DATETIME,                     -- 发货时间
    ship_method TEXT,                       -- 发货方式: auto/manual
    logistics_company TEXT,                 -- 物流公司
    tracking_number TEXT,                   -- 快递单号
    ship_content TEXT,                      -- 发货内容(虚拟商品)
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 订单状态变更日志
CREATE TABLE order_status_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    action_type TEXT,                       -- 操作类型: auto/manual/system
    operator TEXT,                          -- 操作者
    remark TEXT,                           -- 备注
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 订单监听处理逻辑

```python
class OrderStatusListener:
    """订单状态监听器"""
    
    async def handle_order_status_message(self, message: dict) -> None:
        """处理订单状态消息"""
        
        order_info = self.extract_order_info(message)
        status = message['3']['redReminder']
        
        if status == '等待买家付款':
            await self.handle_pending_payment(order_info)
            
        elif status == '等待卖家发货':  # 🎯 关键状态：用户已付款
            await self.handle_payment_confirmed(order_info)
            
        elif status == '交易关闭':
            await self.handle_order_cancelled(order_info)
            
    async def handle_payment_confirmed(self, order_info: dict) -> None:
        """处理用户付款确认"""
        item_id = order_info['item_id']
        
        # 检查商品配置
        product_config = self.product_manager.get_product_config(item_id)
        
        if product_config and product_config['auto_ship']:
            # 自动发货流程
            await self.schedule_auto_ship(order_info, product_config)
        else:
            # 手动发货通知流程  
            await self.send_manual_ship_notification(order_info)
```

---

## 🤖 自动发货系统设计

### 发货处理流程

```python
class AutoShipSystem:
    """自动发货系统"""
    
    async def schedule_auto_ship(self, order_info: dict, product_config: dict) -> None:
        """调度自动发货任务"""
        
        # 计算发货延时
        delay = self.calculate_ship_delay(product_config)
        
        # 创建异步发货任务
        task = asyncio.create_task(
            self.delayed_auto_ship(order_info, product_config, delay)
        )
        
        # 记录任务
        self.pending_ship_tasks[order_info['order_id']] = task
        
    async def delayed_auto_ship(self, order_info: dict, config: dict, delay_minutes: int) -> None:
        """延时自动发货"""
        
        # 等待指定时间
        await asyncio.sleep(delay_minutes * 60)
        
        try:
            # 执行发货
            result = await self.execute_ship(order_info, config)
            
            if result['success']:
                # 发货成功处理
                await self.handle_ship_success(order_info, result)
            else:
                # 发货失败处理
                await self.handle_ship_failure(order_info, result)
                
        except Exception as e:
            logger.error(f"自动发货异常: {e}")
            await self.handle_ship_error(order_info, str(e))
```

### 闲鱼发货API扩展

```python
# XianyuApis.py 扩展

def ship_order(self, order_id: str, logistics_company: str = "顺丰快递", 
               tracking_number: str = "", retry_count: int = 0) -> dict:
    """发货接口 - 标记订单为已发货状态"""
    
def get_order_list(self, page: int = 1, page_size: int = 20, 
                   status: str = "ALL", retry_count: int = 0) -> dict:
    """获取订单列表"""
    
def get_order_detail(self, order_id: str, retry_count: int = 0) -> dict:
    """获取订单详情"""
    
def generate_tracking_number(self, prefix: str = "SF") -> str:
    """生成模拟快递单号"""
```

---

## 🔔 通知系统设计

### 通知渠道支持

```python
class NotificationSystem:
    """通知系统"""
    
    def __init__(self):
        self.wechat_bot = WeChatBot()
        self.sms_service = SMSService() 
        self.email_service = EmailService()
        
    async def send_ship_notification(self, order_info: dict, config: dict) -> bool:
        """发送发货提醒通知"""
        
        message = self.format_ship_message(order_info)
        success = False
        
        # 微信通知
        if config.get('wechat_enabled', True):
            success |= await self.wechat_bot.send_message(message)
            
        # 短信通知
        if config.get('sms_enabled', False):
            success |= await self.sms_service.send_sms(
                config['phone_number'], message
            )
            
        # 邮件通知（备用）
        if not success and config.get('email_enabled', False):
            success |= await self.email_service.send_email(
                config['email'], "发货提醒", message
            )
            
        return success
```

### 微信机器人实现

```python
class WeChatBot:
    """企业微信机器人"""
    
    def __init__(self):
        self.webhook_url = os.getenv('WECHAT_BOT_WEBHOOK_URL')
        self.mention_users = os.getenv('WECHAT_MENTION_USERS', '@all')
        
    async def send_message(self, message: str) -> bool:
        """发送微信消息"""
        data = {
            "msgtype": "text",
            "text": {
                "content": f"{message}\n{self.mention_users}",
                "mentioned_list": [self.mention_users] if self.mention_users != '@all' else None
            }
        }
        
        # HTTP请求发送消息...
```

### 环境配置扩展

```python
# .env 配置扩展

# 自动发货配置
AUTO_SHIP_ENABLED=true                    # 是否启用自动发货
AUTO_SHIP_DELAY_MIN=30                   # 最小发货延时(分钟)  
AUTO_SHIP_DELAY_MAX=120                  # 最大发货延时(分钟)
AUTO_SHIP_VIRTUAL_DELAY=0                # 虚拟商品发货延时(分钟)
AUTO_SHIP_LOGISTICS_COMPANY=顺丰快递      # 默认物流公司
AUTO_SHIP_TRACKING_PREFIX=SF            # 快递单号前缀
AUTO_SHIP_MAX_RETRIES=3                 # 发货失败最大重试次数
AUTO_SHIP_RETRY_DELAY=300               # 重试间隔(秒)

# 商品分类配置
VIRTUAL_PRODUCT_KEYWORDS=激活码,软件,充值,会员,代充  # 虚拟商品关键词
PHYSICAL_PRODUCT_KEYWORDS=手机,电脑,包包,衣服      # 实物商品关键词

# 微信通知配置
WECHAT_NOTIFICATION_ENABLED=true
WECHAT_BOT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
WECHAT_MENTION_USERS=@all

# 短信通知配置  
SMS_NOTIFICATION_ENABLED=false
SMS_ACCESS_KEY=your_access_key
SMS_ACCESS_SECRET=your_secret
SMS_SIGN_NAME=闲鱼小店
SMS_TEMPLATE_CODE=SMS_123456
SMS_PHONE_NUMBER=13800138000

# 邮件通知配置
EMAIL_NOTIFICATION_ENABLED=false
EMAIL_SMTP_HOST=smtp.qq.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@qq.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO_ADDRESS=your_email@qq.com
```

---

## 🖥️ Web管理后台设计

### 页面结构

```
管理后台 (基于现有Flask应用扩展)
├── 首页Dashboard
│   ├── 今日订单统计
│   ├── 发货待处理数量
│   ├── 自动发货成功率
│   └── 系统状态监控
├── 商品管理
│   ├── 商品配置列表
│   ├── 添加/编辑商品配置
│   ├── 批量导入商品
│   └── 库存管理
├── 订单管理  
│   ├── 订单列表
│   ├── 订单详情
│   ├── 发货记录
│   └── 异常订单处理
├── 通知设置
│   ├── 微信机器人配置
│   ├── 短信服务配置
│   └── 通知测试
└── 系统日志
    ├── 发货日志
    ├── 错误日志
    └── 操作日志
```

### Flask路由设计

```python
# web_admin.py - 扩展现有的web应用

# 首页Dashboard
@app.route('/admin')
def admin_dashboard():
    """管理后台首页"""

# 商品管理
@app.route('/admin/products')
def product_list():
    """商品配置列表"""

@app.route('/admin/api/products', methods=['POST'])
def api_create_product():
    """创建商品配置API"""

# 订单管理
@app.route('/admin/orders')
def order_list():
    """订单列表"""

@app.route('/admin/orders/<order_id>')
def order_detail(order_id):
    """订单详情"""
```

---

## 📁 项目文件结构

```
XianyuAutoAgent/
├── main.py                    # 主程序入口(扩展)
├── XianyuApis.py             # 闲鱼API封装(扩展)  
├── context_manager.py        # 对话上下文管理(扩展)
├── XianyuAgent.py           # AI回复机器人(现有)
│
├── order_system/            # 订单管理系统 🆕
│   ├── __init__.py
│   ├── order_manager.py     # 订单管理器
│   ├── product_config.py    # 商品配置管理  
│   ├── auto_ship.py         # 自动发货系统
│   └── order_database.py    # 订单数据库操作
│
├── notification/            # 通知系统 🆕
│   ├── __init__.py
│   ├── notification_manager.py  # 通知管理器
│   ├── wechat_bot.py        # 微信机器人
│   ├── sms_service.py       # 短信服务
│   └── email_service.py     # 邮件服务
│
├── web_admin/               # Web管理后台 🆕
│   ├── __init__.py
│   ├── admin_app.py         # Flask管理应用
│   ├── templates/           # 页面模板
│   │   └── admin/
│   │       ├── dashboard.html
│   │       ├── products.html
│   │       └── orders.html
│   └── static/              # 静态资源
│       ├── css/
│       └── js/
│
├── data/                    # 数据目录(扩展)
│   ├── chat_history.db      # 对话历史(现有)
│   ├── orders.db           # 订单数据库 🆕
│   └── product_configs.db   # 商品配置数据库 🆕
│
└── utils/                   # 工具函数
    ├── __init__.py
    ├── xianyu_utils.py      # 闲鱼工具(现有)
    └── common_utils.py      # 通用工具 🆕
```

---

## 🚀 实施计划

### Phase 1: 基础架构 (Week 1) - **核心必要**
- ✅ 完善XianyuApis订单相关接口
- ✅ 扩展数据库结构 
- ✅ 创建商品配置管理系统
- ✅ 集成到现有main.py流程

### Phase 2: 自动发货系统 (Week 2) - **核心必要**
- ✅ 实现订单状态监听增强
- ✅ 开发自动发货逻辑
- ✅ 添加发货API调用
- ✅ 库存管理功能

### Phase 3: 通知系统 (Week 3) - **高优先级**
- ✅ 微信机器人集成
- ✅ 短信服务集成  
- ✅ 通知模板和配置
- ✅ 发货提醒功能

### Phase 4: 管理后台 (Week 4) - **中优先级**
- ✅ Web管理界面开发
- ✅ 商品配置页面
- ✅ 订单管理页面
- ✅ 数据统计和日志

### Phase 5: 测试和优化 (Week 5) - **后期优化**
- ✅ 系统集成测试
- ✅ 性能优化
- ✅ 错误处理完善
- ✅ 文档和使用说明

---

## 🎯 功能优先级评估

### 🔥 核心必要功能
1. **订单状态监听** - 检测用户付款，触发后续流程
2. **商品配置管理** - 设置哪些商品自动发货，哪些手动发货  
3. **自动发货系统** - 虚拟商品/配置商品自动发货
4. **基础通知** - 至少微信机器人通知手动发货

### 🌟 高价值功能
1. **发货延时控制** - 模拟人工发货时间
2. **库存管理** - 防止超卖
3. **发货记录追踪** - 完整的操作日志
4. **错误处理重试** - 提高系统稳定性

### 💎 增值功能
1. **Web管理后台** - 可视化配置界面
2. **多种通知渠道** - 短信、邮件备用通知
3. **数据统计分析** - 销售和发货数据报表
4. **批量操作** - 批量商品配置管理

### 🎨 锦上添花功能
1. **高级发货模板** - 个性化发货内容
2. **智能物流选择** - 根据地区自动选择物流
3. **客户标签管理** - VIP客户特殊处理
4. **营销活动集成** - 促销活动自动化

---

## 📝 技术实现说明

### 现有系统集成
- 基于现有WebSocket消息处理流程扩展
- 复用现有数据库和配置系统
- 保持现有AI客服功能不变
- 渐进式扩展，不影响现有功能

### 关键技术点
- **异步处理**: 使用asyncio处理发货延时和并发
- **状态持久化**: SQLite数据库存储订单和配置
- **模块化设计**: 独立的订单系统和通知系统
- **配置驱动**: 环境变量控制所有功能开关
- **错误恢复**: 完善的重试机制和异常处理

### 性能考虑
- 数据库索引优化查询性能
- 异步任务避免阻塞主流程  
- 缓存机制减少API调用
- 批量处理提高吞吐量

---

这个设计文档涵盖了从基础功能到高级特性的完整方案，你可以根据实际需求和资源情况选择实施的功能模块。建议优先实现核心必要功能，然后根据使用情况逐步扩展。