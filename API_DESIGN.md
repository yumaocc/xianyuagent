# 🔌 闲鱼店铺自动化管理系统API设计文档

## 📋 API概览

本系统提供完整的RESTful API接口，支持商品配置管理、订单状态查询、发货操作控制等功能。

---

## 🌐 API基础信息

### 基础配置
- **Base URL**: `http://localhost:8080/api/v1`
- **认证方式**: Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8
- **API版本**: v1.0

### 响应格式标准

```json
{
    "success": true,
    "code": 200,
    "message": "操作成功",
    "data": {
        // 具体数据内容
    },
    "timestamp": "2025-01-15T10:30:00Z"
}
```

### 错误响应格式

```json
{
    "success": false,
    "code": 400,
    "message": "请求参数错误",
    "error": {
        "type": "ValidationError",
        "details": "item_id字段不能为空"
    },
    "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## 📦 商品配置管理API

### 1. 获取商品配置列表

**接口描述**: 获取所有商品的配置信息

```http
GET /api/v1/products/configs
```

**请求参数**:
```
Query Parameters:
- page: int (可选) - 页码，默认1
- size: int (可选) - 每页数量，默认20
- status: string (可选) - 商品状态 active/inactive/out_of_stock
- category: string (可选) - 商品类型 virtual/physical
- auto_ship: boolean (可选) - 是否自动发货
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "total": 156,
        "page": 1,
        "size": 20,
        "items": [
            {
                "item_id": "12345678",
                "title": "iPhone 15 Pro Max",
                "category": "physical",
                "auto_ship": false,
                "ship_delay_min": 30,
                "ship_delay_max": 120,
                "logistics_company": "顺丰快递",
                "stock_quantity": 50,
                "status": "active",
                "created_time": "2025-01-10T09:00:00Z",
                "updated_time": "2025-01-15T10:30:00Z"
            }
        ]
    }
}
```

### 2. 获取单个商品配置

**接口描述**: 根据商品ID获取具体配置信息

```http
GET /api/v1/products/configs/{item_id}
```

**路径参数**:
- `item_id`: string - 商品ID

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "item_id": "12345678",
        "title": "iPhone 15 Pro Max",
        "category": "physical",
        "auto_ship": false,
        "ship_delay_min": 30,
        "ship_delay_max": 120,
        "logistics_company": "顺丰快递",
        "ship_template": null,
        "stock_quantity": 50,
        "status": "active",
        "created_time": "2025-01-10T09:00:00Z",
        "updated_time": "2025-01-15T10:30:00Z"
    }
}
```

### 3. 创建商品配置

**接口描述**: 为商品添加自动化配置

```http
POST /api/v1/products/configs
```

**请求体**:
```json
{
    "item_id": "12345678",
    "title": "iPhone 15 Pro Max",
    "category": "physical",
    "auto_ship": false,
    "ship_delay_min": 30,
    "ship_delay_max": 120,
    "logistics_company": "顺丰快递",
    "ship_template": "",
    "stock_quantity": 50,
    "status": "active"
}
```

**字段说明**:
- `item_id`: string (必填) - 商品ID
- `title`: string (必填) - 商品标题
- `category`: string (必填) - 商品类型 virtual/physical
- `auto_ship`: boolean (可选) - 是否自动发货，默认false
- `ship_delay_min`: int (可选) - 最小发货延时(分钟)，默认5
- `ship_delay_max`: int (可选) - 最大发货延时(分钟)，默认30
- `logistics_company`: string (可选) - 物流公司，默认"顺丰快递"
- `ship_template`: string (可选) - 发货模板内容(虚拟商品用)
- `stock_quantity`: int (可选) - 库存数量，-1表示无限，默认-1
- `status`: string (可选) - 状态 active/inactive，默认active

### 4. 更新商品配置

**接口描述**: 更新现有商品的配置信息

```http
PUT /api/v1/products/configs/{item_id}
```

**请求体**: 同创建接口，所有字段可选

### 5. 删除商品配置

**接口描述**: 删除商品配置

```http
DELETE /api/v1/products/configs/{item_id}
```

### 6. 批量导入商品配置

**接口描述**: 通过Excel/CSV文件批量导入商品配置

```http
POST /api/v1/products/configs/batch-import
```

**请求类型**: multipart/form-data

**请求参数**:
- `file`: File - Excel或CSV文件
- `overwrite`: boolean (可选) - 是否覆盖已存在配置，默认false

---

## 📋 订单管理API

### 1. 获取订单列表

**接口描述**: 获取订单列表信息

```http
GET /api/v1/orders
```

**请求参数**:
```
Query Parameters:
- page: int (可选) - 页码，默认1
- size: int (可选) - 每页数量，默认20
- status: string (可选) - 订单状态
- start_date: string (可选) - 开始日期 YYYY-MM-DD
- end_date: string (可选) - 结束日期 YYYY-MM-DD
- user_id: string (可选) - 买家ID
- item_id: string (可选) - 商品ID
- ship_method: string (可选) - 发货方式 auto/manual
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "total": 1240,
        "page": 1,
        "size": 20,
        "items": [
            {
                "order_id": "ORD20250115001",
                "chat_id": "CHAT123456",
                "user_id": "USER789",
                "item_id": "12345678",
                "item_title": "iPhone 15 Pro Max",
                "amount": 8999.00,
                "status": "已发货",
                "payment_time": "2025-01-15T09:30:00Z",
                "ship_time": "2025-01-15T10:15:00Z",
                "ship_method": "auto",
                "logistics_company": "顺丰快递",
                "tracking_number": "SF1234567890",
                "created_time": "2025-01-15T09:00:00Z"
            }
        ]
    }
}
```

### 2. 获取订单详情

**接口描述**: 根据订单ID获取详细信息

```http
GET /api/v1/orders/{order_id}
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "order_id": "ORD20250115001",
        "chat_id": "CHAT123456",
        "user_id": "USER789",
        "item_id": "12345678",
        "item_title": "iPhone 15 Pro Max",
        "amount": 8999.00,
        "status": "已发货",
        "payment_time": "2025-01-15T09:30:00Z",
        "ship_time": "2025-01-15T10:15:00Z",
        "ship_method": "auto",
        "logistics_company": "顺丰快递",
        "tracking_number": "SF1234567890",
        "ship_content": null,
        "created_time": "2025-01-15T09:00:00Z",
        "updated_time": "2025-01-15T10:15:00Z",
        "status_logs": [
            {
                "from_status": "等待买家付款",
                "to_status": "等待卖家发货",
                "action_type": "system",
                "operator": "system",
                "remark": "买家付款成功",
                "created_time": "2025-01-15T09:30:00Z"
            },
            {
                "from_status": "等待卖家发货",
                "to_status": "已发货",
                "action_type": "auto",
                "operator": "auto_ship_system",
                "remark": "自动发货成功",
                "created_time": "2025-01-15T10:15:00Z"
            }
        ]
    }
}
```

### 3. 手动发货

**接口描述**: 手动标记订单为已发货状态

```http
POST /api/v1/orders/{order_id}/ship
```

**请求体**:
```json
{
    "logistics_company": "顺丰快递",
    "tracking_number": "SF1234567890",
    "remark": "已发货，请注意查收"
}
```

### 4. 获取订单统计

**接口描述**: 获取订单相关统计数据

```http
GET /api/v1/orders/statistics
```

**请求参数**:
```
Query Parameters:
- date_range: string (可选) - 统计范围 today/week/month/year，默认today
- start_date: string (可选) - 开始日期 YYYY-MM-DD
- end_date: string (可选) - 结束日期 YYYY-MM-DD
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "total_orders": 156,
        "pending_payment": 12,
        "pending_ship": 8,
        "shipped": 120,
        "completed": 110,
        "cancelled": 6,
        "auto_ship_count": 95,
        "manual_ship_count": 25,
        "auto_ship_success_rate": 0.95,
        "total_amount": 125680.50,
        "average_ship_delay": 45.6
    }
}
```

---

## 🚚 发货管理API

### 1. 获取发货任务列表

**接口描述**: 获取所有发货任务的状态

```http
GET /api/v1/shipping/tasks
```

**请求参数**:
```
Query Parameters:
- page: int (可选) - 页码，默认1
- size: int (可选) - 每页数量，默认20
- status: string (可选) - 任务状态 scheduled/waiting/executing/succeeded/failed/cancelled
- order_id: string (可选) - 订单ID
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "total": 45,
        "page": 1,
        "size": 20,
        "items": [
            {
                "task_id": "TASK20250115001",
                "order_id": "ORD20250115001",
                "status": "succeeded",
                "scheduled_time": "2025-01-15T09:30:00Z",
                "execute_time": "2025-01-15T10:15:00Z",
                "retry_count": 0,
                "error_msg": null,
                "created_time": "2025-01-15T09:30:00Z"
            }
        ]
    }
}
```

### 2. 取消发货任务

**接口描述**: 取消指定的自动发货任务

```http
DELETE /api/v1/shipping/tasks/{task_id}
```

**路径参数**:
- `task_id`: string - 发货任务ID

### 3. 重新执行发货任务

**接口描述**: 重新执行失败的发货任务

```http
POST /api/v1/shipping/tasks/{task_id}/retry
```

### 4. 获取发货日志

**接口描述**: 获取发货操作的详细日志

```http
GET /api/v1/shipping/logs
```

**请求参数**:
```
Query Parameters:
- page: int (可选) - 页码，默认1
- size: int (可选) - 每页数量，默认50
- order_id: string (可选) - 订单ID
- action: string (可选) - 操作类型
- start_date: string (可选) - 开始日期
- end_date: string (可选) - 结束日期
```

---

## 🔔 通知管理API

### 1. 获取通知配置

**接口描述**: 获取当前通知系统配置

```http
GET /api/v1/notifications/config
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "wechat": {
            "enabled": true,
            "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
            "mention_users": "@all"
        },
        "sms": {
            "enabled": false,
            "phone_number": "13800138000",
            "template_code": "SMS_123456"
        },
        "email": {
            "enabled": false,
            "smtp_host": "smtp.qq.com",
            "to_address": "admin@example.com"
        }
    }
}
```

### 2. 更新通知配置

**接口描述**: 更新通知系统配置

```http
PUT /api/v1/notifications/config
```

**请求体**: 同获取配置响应格式

### 3. 测试通知发送

**接口描述**: 发送测试通知消息

```http
POST /api/v1/notifications/test
```

**请求体**:
```json
{
    "channel": "wechat",  // wechat/sms/email
    "message": "这是一条测试消息"
}
```

### 4. 获取通知历史

**接口描述**: 获取通知发送历史记录

```http
GET /api/v1/notifications/history
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "total": 89,
        "items": [
            {
                "id": 1,
                "order_id": "ORD20250115001",
                "channel": "wechat",
                "message": "订单ORD20250115001需要手动发货",
                "status": "success",
                "error_msg": null,
                "created_time": "2025-01-15T10:30:00Z"
            }
        ]
    }
}
```

---

## 📊 库存管理API

### 1. 获取库存列表

**接口描述**: 获取所有商品的库存信息

```http
GET /api/v1/inventory
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "items": [
            {
                "item_id": "12345678",
                "title": "iPhone 15 Pro Max",
                "current_stock": 45,
                "reserved_stock": 5,
                "available_stock": 40,
                "low_stock_threshold": 10,
                "status": "normal",
                "last_updated": "2025-01-15T10:30:00Z"
            }
        ]
    }
}
```

### 2. 更新库存

**接口描述**: 手动调整商品库存

```http
POST /api/v1/inventory/{item_id}/adjust
```

**请求体**:
```json
{
    "quantity_change": 10,  // 正数增加，负数减少
    "reason": "手动补货",
    "remark": "采购入库"
}
```

### 3. 获取库存变更日志

**接口描述**: 获取库存变更历史记录

```http
GET /api/v1/inventory/{item_id}/logs
```

---

## 📈 数据统计API

### 1. 获取系统概览统计

**接口描述**: 获取系统运行概览数据

```http
GET /api/v1/statistics/overview
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "today_orders": 28,
        "pending_ships": 5,
        "auto_ship_success_rate": 0.952,
        "system_uptime": "5天12小时30分钟",
        "total_products": 156,
        "active_products": 142,
        "low_stock_products": 8,
        "notification_success_rate": 0.98
    }
}
```

### 2. 获取销售统计

**接口描述**: 获取销售数据统计

```http
GET /api/v1/statistics/sales
```

**请求参数**:
```
Query Parameters:
- date_range: string (可选) - 统计范围 7d/30d/90d，默认30d
- group_by: string (可选) - 分组方式 day/week/month，默认day
```

### 3. 获取发货效率统计

**接口描述**: 获取发货效率相关统计

```http
GET /api/v1/statistics/shipping
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "auto_ship_rate": 0.78,
        "average_ship_delay": 42.5,
        "ship_success_rate": 0.952,
        "virtual_product_rate": 0.35,
        "peak_hours": ["10:00-12:00", "14:00-16:00"],
        "daily_stats": [
            {
                "date": "2025-01-15",
                "total_ships": 25,
                "auto_ships": 20,
                "success_ships": 24,
                "average_delay": 38.5
            }
        ]
    }
}
```

---

## 🔧 系统管理API

### 1. 获取系统状态

**接口描述**: 获取系统运行状态信息

```http
GET /api/v1/system/status
```

**响应示例**:
```json
{
    "success": true,
    "code": 200,
    "message": "查询成功",
    "data": {
        "status": "running",
        "uptime": "5天12小时30分钟",
        "version": "1.0.0",
        "websocket_status": "connected",
        "database_status": "healthy",
        "api_status": "normal",
        "memory_usage": 0.67,
        "cpu_usage": 0.23,
        "disk_usage": 0.45
    }
}
```

### 2. 系统健康检查

**接口描述**: 系统健康状况检查

```http
GET /api/v1/system/health
```

### 3. 获取系统日志

**接口描述**: 获取系统运行日志

```http
GET /api/v1/system/logs
```

**请求参数**:
```
Query Parameters:
- level: string (可选) - 日志级别 DEBUG/INFO/WARNING/ERROR
- start_time: string (可选) - 开始时间
- end_time: string (可选) - 结束时间
- limit: int (可选) - 返回条数，默认100
```

---

## 🔐 认证授权

### JWT Token认证

**获取Token**:
```http
POST /api/v1/auth/login
```

**请求体**:
```json
{
    "username": "admin",
    "password": "your_password"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "expires_in": 3600
    }
}
```

**使用Token**:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📝 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token无效 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 429 | 请求频率限制 |
| 500 | 服务器内部错误 |
| 502 | 网关错误 |
| 503 | 服务不可用 |

---

## 🔄 API版本控制

### 版本策略
- URL路径版本控制: `/api/v1/`, `/api/v2/`
- 向后兼容原则：新版本保持对旧版本的兼容
- 废弃策略：废弃的API会提前3个月通知

### 版本变更记录
- **v1.0** (2025-01-15): 初始版本发布
- **v1.1** (计划): 增加批量操作接口
- **v2.0** (计划): GraphQL支持

---

这个API文档为系统的所有功能提供了完整的接口规范，便于前端开发和第三方系统集成。