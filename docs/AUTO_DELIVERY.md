# 自动发货功能使用指南

## 功能概述

自动发货功能专为虚拟商品设计，支持在买家付款后自动发送商品信息（如网盘链接、卡密等）。

## 核心特性

- ✅ **多种发货类型**：支持网盘链接、卡密、自定义文本
- ✅ **自定义消息模板**：支持个性化发货消息
- ✅ **库存管理**：支持设置库存数量（-1表示无限）
- ✅ **发货记录**：完整的发货日志和统计
- ✅ **灵活配置**：每个商品可单独配置发货信息

## 快速开始

### 1. 配置商品发货信息

通过Web API为商品配置发货信息：

```bash
POST /api/delivery/configs/{item_id}
Content-Type: application/json

{
  "delivery_type": "netdisk",           # 发货类型: netdisk/cardkey/text
  "delivery_content": "https://pan.baidu.com/s/xxxxx",  # 发货内容
  "extraction_code": "abcd",            # 提取码（可选）
  "custom_message": "",                 # 自定义消息模板（可选）
  "is_enabled": true,                   # 是否启用自动发货
  "stock_count": -1                     # 库存数量（-1表示无限）
}
```

### 2. 发货类型说明

#### 网盘链接 (netdisk)
```json
{
  "delivery_type": "netdisk",
  "delivery_content": "https://pan.baidu.com/s/xxxxx",
  "extraction_code": "abcd"
}
```

**默认发货消息格式**：
```
您好！感谢购买，以下是商品资源：

📦 网盘链接：https://pan.baidu.com/s/xxxxx
🔑 提取码：abcd

请及时保存，如有问题请随时联系我。祝您使用愉快！
```

#### 卡密 (cardkey)
```json
{
  "delivery_type": "cardkey",
  "delivery_content": "XXXX-XXXX-XXXX-XXXX"
}
```

**默认发货消息格式**：
```
您好！感谢购买，以下是您的卡密信息：

🎟️ 卡密：XXXX-XXXX-XXXX-XXXX

请妥善保管，如有问题请随时联系我。
```

#### 自定义文本 (text)
```json
{
  "delivery_type": "text",
  "delivery_content": "您的自定义发货内容"
}
```

### 3. 自定义消息模板

支持使用变量占位符：

```json
{
  "delivery_type": "netdisk",
  "delivery_content": "https://pan.baidu.com/s/xxxxx",
  "extraction_code": "abcd",
  "custom_message": "亲爱的客户，您购买的【{title}】已发货！\n\n网盘：{content}\n提取码：{code}\n\n价格：{price}元\n\n感谢支持！"
}
```

**可用变量**：
- `{content}` - 发货内容（网盘链接/卡密等）
- `{code}` - 提取码
- `{title}` - 商品标题
- `{price}` - 商品价格

### 4. 库存管理

```json
{
  "stock_count": -1    # -1表示无限库存
}
```

或

```json
{
  "stock_count": 100   # 有限库存，每次发货自动减1
}
```

当库存不足时，系统会自动发送提醒消息给买家。

## API接口文档

### 发货配置管理

#### 获取所有发货配置
```http
GET /api/delivery/configs?enabled_only=false
```

**响应**：
```json
{
  "status": "success",
  "data": [
    {
      "item_id": "123456",
      "delivery_type": "netdisk",
      "delivery_content": "https://pan.baidu.com/s/xxxxx",
      "extraction_code": "abcd",
      "is_enabled": true,
      "stock_count": -1,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

#### 获取单个商品配置
```http
GET /api/delivery/configs/{item_id}
```

#### 保存/更新配置
```http
POST /api/delivery/configs/{item_id}
PUT /api/delivery/configs/{item_id}
```

#### 删除配置
```http
DELETE /api/delivery/configs/{item_id}
```

### 发货记录查询

#### 获取发货记录
```http
GET /api/delivery/records?item_id={item_id}&buyer_id={buyer_id}&limit=100
```

**响应**：
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "order_id": "",
      "item_id": "123456",
      "buyer_id": "buyer123",
      "chat_id": "chat123",
      "delivery_type": "netdisk",
      "delivery_content": "https://pan.baidu.com/s/xxxxx",
      "delivery_time": "2024-01-01T00:00:00",
      "status": "success",
      "error_message": ""
    }
  ]
}
```

#### 获取发货统计
```http
GET /api/delivery/stats
```

**响应**：
```json
{
  "status": "success",
  "data": {
    "total_configs": 10,      // 总配置数
    "enabled_configs": 8,     // 已启用配置数
    "total_deliveries": 100,  // 总发货次数
    "success_deliveries": 98, // 成功发货次数
    "success_rate": 98.0      // 成功率(%)
  }
}
```

## 工作流程

1. **买家下单付款** → 闲鱼订单状态变为"等待卖家发货"
2. **系统接收订单消息** → main.py中的订单监听器捕获
3. **检查发货配置** → 查询该商品是否配置了自动发货
4. **验证库存** → 检查库存是否充足
5. **构建发货消息** → 根据配置生成发货消息
6. **发送消息** → 通过WebSocket发送给买家
7. **记录发货** → 保存发货记录到数据库
8. **更新库存** → 减少库存数量（如果不是无限库存）

## 数据存储

发货功能支持两种存储模式：

### SQLite数据库模式（推荐）
- 数据库文件：`data/delivery.db`
- 表结构：
  - `delivery_configs` - 发货配置表
  - `delivery_records` - 发货记录表

### 文件模式（无SQLite环境）
- 配置文件：`data/delivery_configs.json`
- 记录文件：`data/delivery_records.json`

## 日志示例

```
2024-01-01 12:00:00 | INFO | 💰 交易成功 https://www.goofish.com/personal?userId=123 等待卖家发货 - 商品ID: 123456
2024-01-01 12:00:00 | INFO | 📦 开始处理自动发货: 商品123456, 买家123
2024-01-01 12:00:00 | INFO | 📤 发送发货消息给买家123
2024-01-01 12:00:00 | INFO | ✅ 自动发货成功: 商品123456, 买家123
```

## 常见问题

### Q: 如何禁用某个商品的自动发货？
A: 通过API更新配置，设置 `is_enabled: false`

### Q: 库存不足怎么办？
A: 系统会自动发送"抱歉，该商品暂时缺货，请联系卖家处理"的消息给买家，并记录发货失败。

### Q: 如何查看发货是否成功？
A: 通过 `/api/delivery/records` 查看发货记录，或查看系统日志。

### Q: 支持批量导入发货配置吗？
A: 目前需要通过API逐个配置，后续可扩展批量导入功能。

### Q: 可以为不同商品设置不同的发货内容吗？
A: 完全可以！每个商品都有独立的发货配置。

## 注意事项

⚠️ **重要提示**：
- 请确保发货内容（网盘链接、卡密等）的有效性
- 建议定期检查库存状态
- 发货消息一旦发送无法撤回，请仔细核对配置
- 建议在测试环境先测试自动发货流程
- 网盘链接建议使用永久有效链接

## 扩展建议

未来可扩展的功能：
- [ ] 多卡密池管理（自动分配未使用的卡密）
- [ ] 发货通知（邮件/微信提醒卖家）
- [ ] 批量导入/导出配置
- [ ] 发货模板库
- [ ] 定时清理过期记录
- [ ] 发货数据统计图表

## 技术实现

核心文件：
- `delivery_manager.py` - 发货管理器（~800行）
- `main.py` - 订单监听和自动发货逻辑（新增~90行）
- `web_api.py` - RESTful API接口（新增~150行）

数据库表设计详见 `delivery_manager.py:_init_db()`
