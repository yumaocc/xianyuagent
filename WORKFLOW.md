# 🔄 闲鱼店铺自动化管理系统工作流程

## 📋 总体业务流程概览

```mermaid
graph TD
    subgraph "用户交互流程"
        USER[用户咨询] --> CHAT[智能客服回复]
        CHAT --> NEGO[议价协商]
        NEGO --> DEAL[促成交易]
        DEAL --> ORDER[用户下单付款]
    end
    
    subgraph "订单自动化流程"
        ORDER --> DETECT[检测付款状态]
        DETECT --> CONFIG[检查商品配置]
        CONFIG --> AUTO{是否自动发货?}
        
        AUTO -->|是| DELAY[计算发货延时]
        AUTO -->|否| NOTIFY[发送发货提醒]
        
        DELAY --> SHIP[自动发货]
        NOTIFY --> MANUAL[人工发货]
        
        SHIP --> SUCCESS{发货成功?}
        SUCCESS -->|是| COMPLETE[完成发货]
        SUCCESS -->|否| RETRY[重试发货]
        RETRY --> SHIP
        
        MANUAL --> TRACK[跟踪发货状态]
        COMPLETE --> STATS[更新统计数据]
        TRACK --> STATS
    end
    
    style ORDER fill:#e8f5e8
    style AUTO fill:#e3f2fd
    style SHIP fill:#f1f8e9
    style NOTIFY fill:#fff3e0
```

---

## 🎯 详细工作流程

### 1. 用户咨询处理流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant XY as 闲鱼平台
    participant MP as 消息处理中心
    participant AI as AI客服系统
    participant EX as 专家系统
    participant CM as 上下文管理器
    
    U->>XY: 发送咨询消息
    XY->>MP: WebSocket推送消息
    MP->>CM: 保存对话历史
    MP->>AI: 处理用户消息
    
    AI->>AI: 意图识别分类
    
    alt 议价咨询
        AI->>EX: 调用议价专家
        EX->>EX: 分析价格策略
        EX-->>AI: 返回议价回复
    else 技术咨询  
        AI->>EX: 调用技术专家
        EX->>EX: 搜索技术资料
        EX-->>AI: 返回技术解答
    else 一般咨询
        AI->>EX: 调用默认专家
        EX-->>AI: 返回通用回复
    end
    
    AI->>CM: 保存AI回复
    AI->>XY: 发送回复消息
    XY->>U: 用户收到回复
    
    Note over U,CM: 持续对话直到促成交易
```

### 2. 订单状态监听流程

```mermaid
flowchart TD
    START([闲鱼推送订单消息]) --> PARSE[解析消息内容]
    PARSE --> VALIDATE[验证消息格式]
    VALIDATE --> EXTRACT[提取订单信息]
    
    EXTRACT --> ORDER_ID[订单ID]
    EXTRACT --> USER_ID[用户ID]  
    EXTRACT --> ITEM_ID[商品ID]
    EXTRACT --> STATUS[订单状态]
    EXTRACT --> AMOUNT[交易金额]
    
    STATUS --> CHECK{状态类型判断}
    
    CHECK -->|等待买家付款| PENDING_PAY[记录待付款订单]
    CHECK -->|等待卖家发货| PAID_ORDER[处理已付款订单]
    CHECK -->|交易关闭| CANCEL_ORDER[处理取消订单]
    CHECK -->|已发货| SHIP_ORDER[更新发货状态]
    CHECK -->|交易成功| COMPLETE_ORDER[完成交易]
    
    PAID_ORDER --> SAVE_DB[(保存到数据库)]
    SAVE_DB --> TRIGGER[触发发货流程]
    
    PENDING_PAY --> LOG1[记录日志]
    CANCEL_ORDER --> LOG2[记录日志]
    SHIP_ORDER --> LOG3[记录日志]
    COMPLETE_ORDER --> LOG4[记录日志]
    
    LOG1 --> END([流程结束])
    LOG2 --> END
    LOG3 --> END  
    LOG4 --> END
    
    TRIGGER --> NEXT[进入发货处理流程]
    NEXT --> END
    
    style PAID_ORDER fill:#e8f5e8
    style SAVE_DB fill:#e1f5fe
    style TRIGGER fill:#f3e5f5
```

### 3. 自动发货处理流程

```mermaid
graph TD
    START([订单付款确认]) --> GET_CONFIG[获取商品配置]
    GET_CONFIG --> CONFIG_CHECK{配置检查}
    
    CONFIG_CHECK -->|无配置| DEFAULT[使用默认配置]
    CONFIG_CHECK -->|有配置| USE_CONFIG[使用商品配置]
    
    DEFAULT --> MANUAL_FLAG[标记为手动发货]
    USE_CONFIG --> AUTO_CHECK{是否自动发货}
    
    AUTO_CHECK -->|否| MANUAL_FLAG
    AUTO_CHECK -->|是| PRODUCT_TYPE[检查商品类型]
    
    PRODUCT_TYPE --> TYPE_CHECK{商品类型}
    TYPE_CHECK -->|虚拟商品| INSTANT[立即发货模式]
    TYPE_CHECK -->|实物商品| DELAYED[延时发货模式]
    
    INSTANT --> DELAY_0[延时 = 0分钟]
    DELAYED --> CALC_DELAY[计算随机延时]
    CALC_DELAY --> DELAY_RANGE[5-120分钟随机]
    
    DELAY_0 --> SCHEDULE[调度发货任务]
    DELAY_RANGE --> SCHEDULE
    
    SCHEDULE --> ASYNC_TASK[创建异步任务]
    ASYNC_TASK --> WAIT[等待延时时间]
    WAIT --> EXECUTE[执行发货操作]
    
    EXECUTE --> API_CALL[调用闲鱼发货API]
    API_CALL --> API_RESULT{API调用结果}
    
    API_RESULT -->|成功| SUCCESS[发货成功]
    API_RESULT -->|失败| RETRY_CHECK{重试检查}
    API_RESULT -->|网络错误| RETRY_CHECK
    
    RETRY_CHECK -->|未达重试限制| RETRY_DELAY[等待重试延时]
    RETRY_CHECK -->|达到重试限制| FAIL_ALERT[发送失败告警]
    
    RETRY_DELAY --> API_CALL
    
    SUCCESS --> UPDATE_ORDER[更新订单状态]
    UPDATE_ORDER --> UPDATE_STOCK[更新库存]
    UPDATE_STOCK --> LOG_SUCCESS[记录成功日志]
    LOG_SUCCESS --> END([流程结束])
    
    MANUAL_FLAG --> SEND_NOTIFY[发送发货提醒]
    SEND_NOTIFY --> END
    
    FAIL_ALERT --> LOG_FAIL[记录失败日志]
    LOG_FAIL --> SEND_NOTIFY
    
    style AUTO_CHECK fill:#e8f5e8
    style EXECUTE fill:#e3f2fd
    style SUCCESS fill:#f1f8e9
    style SEND_NOTIFY fill:#fff3e0
```

### 4. 通知系统处理流程

```mermaid
sequenceDiagram
    participant OS as 订单系统
    participant NS as 通知系统
    participant WX as 微信机器人
    participant SMS as 短信服务
    participant EMAIL as 邮件服务
    participant USER as 店主
    
    OS->>NS: 触发发货提醒
    NS->>NS: 格式化通知消息
    NS->>NS: 检查通知配置
    
    alt 微信通知启用
        NS->>WX: 发送微信消息
        WX->>WX: 构造企业微信消息
        WX-->>NS: 返回发送结果
        
        alt 微信发送成功
            NS->>USER: 微信群收到通知
            NS->>NS: 记录通知成功
        else 微信发送失败
            NS->>SMS: 尝试短信通知
        end
    end
    
    alt 短信通知启用 && 微信失败
        SMS->>SMS: 构造短信内容
        SMS-->>NS: 返回发送结果
        
        alt 短信发送成功
            NS->>USER: 手机收到短信
            NS->>NS: 记录通知成功
        else 短信发送失败
            NS->>EMAIL: 尝试邮件通知
        end
    end
    
    alt 邮件通知启用 && 前面都失败
        EMAIL->>EMAIL: 构造邮件内容
        EMAIL-->>NS: 返回发送结果
        
        alt 邮件发送成功
            NS->>USER: 邮箱收到邮件
            NS->>NS: 记录通知成功
        else 邮件发送失败
            NS->>NS: 记录通知失败
            NS->>NS: 触发系统告警
        end
    end
    
    NS-->>OS: 返回通知结果
```

---

## ⚙️ 配置管理流程

### 1. 商品配置管理流程

```mermaid
flowchart LR
    subgraph "配置入口"
        WEB[Web管理后台]
        API[API接口]
        IMPORT[批量导入]
    end
    
    subgraph "配置处理"
        VALIDATE[数据验证]
        TRANSFORM[数据转换]
        SAVE[保存配置]
        CACHE[更新缓存]
    end
    
    subgraph "配置应用"
        RELOAD[重载配置]
        NOTIFY_SYSTEM[通知系统组件]
        TAKE_EFFECT[配置生效]
    end
    
    WEB --> VALIDATE
    API --> VALIDATE  
    IMPORT --> VALIDATE
    
    VALIDATE --> TRANSFORM
    TRANSFORM --> SAVE
    SAVE --> CACHE
    
    CACHE --> RELOAD
    RELOAD --> NOTIFY_SYSTEM
    NOTIFY_SYSTEM --> TAKE_EFFECT
    
    style VALIDATE fill:#fff3e0
    style SAVE fill:#e8f5e8
    style TAKE_EFFECT fill:#e3f2fd
```

### 2. 系统配置加载流程

```mermaid
stateDiagram-v2
    [*] --> 系统启动
    系统启动 --> 加载环境变量
    加载环境变量 --> 验证必需配置
    验证必需配置 --> 配置验证失败 : 配置缺失
    验证必需配置 --> 初始化数据库 : 配置完整
    
    配置验证失败 --> 输出错误信息
    输出错误信息 --> 系统退出
    
    初始化数据库 --> 加载商品配置
    加载商品配置 --> 初始化通知服务
    初始化通知服务 --> 启动消息监听
    启动消息监听 --> 系统就绪
    
    系统就绪 --> 运行中
    运行中 --> 配置热重载 : 配置变更
    配置热重载 --> 运行中
    
    运行中 --> 系统关闭 : 停止信号
    系统关闭 --> 清理资源
    清理资源 --> [*]
```

---

## 📊 数据处理流程

### 1. 数据库操作流程

```mermaid
graph TD
    subgraph "数据写入流程"
        WRITE_REQ[写入请求] --> VALIDATE_DATA[数据验证]
        VALIDATE_DATA --> TRANSFORM_DATA[数据转换]
        TRANSFORM_DATA --> BEGIN_TX[开始事务]
        BEGIN_TX --> INSERT_DB[插入数据库]
        INSERT_DB --> COMMIT_TX[提交事务]
        COMMIT_TX --> UPDATE_CACHE[更新缓存]
        UPDATE_CACHE --> WRITE_SUCCESS[写入成功]
    end
    
    subgraph "数据读取流程"
        READ_REQ[读取请求] --> CHECK_CACHE[检查缓存]
        CHECK_CACHE --> CACHE_HIT{缓存命中?}
        CACHE_HIT -->|是| RETURN_CACHE[返回缓存数据]
        CACHE_HIT -->|否| QUERY_DB[查询数据库]
        QUERY_DB --> SET_CACHE[设置缓存]
        SET_CACHE --> RETURN_DATA[返回数据]
    end
    
    subgraph "数据同步流程"
        DATA_CHANGE[数据变更] --> INVALIDATE_CACHE[失效缓存]
        INVALIDATE_CACHE --> NOTIFY_SUBSCRIBERS[通知订阅者]
        NOTIFY_SUBSCRIBERS --> UPDATE_VIEWS[更新视图]
    end
    
    style COMMIT_TX fill:#e8f5e8
    style CACHE_HIT fill:#e3f2fd
    style UPDATE_VIEWS fill:#f3e5f5
```

### 2. 库存管理流程

```mermaid
sequenceDiagram
    participant Order as 订单系统
    participant Stock as 库存管理
    participant DB as 数据库
    participant Alert as 告警系统
    
    Order->>Stock: 检查库存
    Stock->>DB: 查询当前库存
    DB-->>Stock: 返回库存数量
    
    alt 库存充足
        Stock-->>Order: 库存可用
        Order->>Stock: 扣减库存
        Stock->>DB: 更新库存数量
        Stock->>DB: 记录库存变更日志
        
        Stock->>Stock: 检查库存阈值
        alt 库存低于阈值
            Stock->>Alert: 发送库存不足告警
        end
        
        Stock-->>Order: 扣减成功
    else 库存不足
        Stock-->>Order: 库存不足
        Order->>Order: 标记商品缺货
        Order->>Alert: 发送缺货告警
    end
```

---

## 🔧 异常处理流程

### 1. 系统异常处理流程

```mermaid
flowchart TD
    EXCEPTION[系统异常] --> CLASSIFY{异常分类}
    
    CLASSIFY -->|网络异常| NETWORK[网络异常处理]
    CLASSIFY -->|API异常| API_ERR[API异常处理]
    CLASSIFY -->|业务异常| BUSINESS[业务异常处理]
    CLASSIFY -->|系统异常| SYSTEM[系统异常处理]
    
    NETWORK --> RETRY_NETWORK[网络重试]
    RETRY_NETWORK --> RETRY_SUCCESS{重试成功?}
    RETRY_SUCCESS -->|是| RECOVER[恢复正常]
    RETRY_SUCCESS -->|否| FAIL_NETWORK[网络失败处理]
    
    API_ERR --> CHECK_API{API错误类型}
    CHECK_API -->|限流| WAIT_API[等待API限流]
    CHECK_API -->|认证失败| REFRESH_AUTH[刷新认证]
    CHECK_API -->|其他| RETRY_API[API重试]
    
    WAIT_API --> RETRY_API
    REFRESH_AUTH --> RETRY_API
    RETRY_API --> RETRY_SUCCESS
    
    BUSINESS --> LOG_BUSINESS[记录业务异常]
    LOG_BUSINESS --> NOTIFY_ADMIN[通知管理员]
    
    SYSTEM --> LOG_SYSTEM[记录系统异常]
    LOG_SYSTEM --> ALERT_SYSTEM[系统告警]
    ALERT_SYSTEM --> RESTART{需要重启?}
    RESTART -->|是| SAFE_RESTART[安全重启]
    RESTART -->|否| CONTINUE[继续运行]
    
    FAIL_NETWORK --> FALLBACK[降级处理]
    SAFE_RESTART --> RECOVER
    CONTINUE --> RECOVER
    FALLBACK --> RECOVER
    NOTIFY_ADMIN --> RECOVER
    
    style EXCEPTION fill:#ffebee
    style RECOVER fill:#e8f5e8
    style FALLBACK fill:#fff3e0
```

### 2. 发货失败处理流程

```mermaid
stateDiagram-v2
    [*] --> 发货执行
    发货执行 --> 发货成功 : API调用成功
    发货执行 --> 发货失败 : API调用失败
    
    发货成功 --> 更新订单状态
    更新订单状态 --> 记录成功日志
    记录成功日志 --> [*]
    
    发货失败 --> 错误分析
    错误分析 --> 网络错误 : 网络问题
    错误分析 --> API错误 : 接口问题
    错误分析 --> 业务错误 : 业务规则
    
    网络错误 --> 检查重试次数
    API错误 --> 检查重试次数
    
    检查重试次数 --> 等待重试 : 未达限制
    检查重试次数 --> 发送告警 : 达到限制
    
    等待重试 --> 重试延时
    重试延时 --> 发货执行
    
    业务错误 --> 记录错误详情
    记录错误详情 --> 发送告警
    
    发送告警 --> 转为手动处理
    转为手动处理 --> 发送通知提醒
    发送通知提醒 --> [*]
```

---

## 📈 监控告警流程

### 1. 系统监控流程

```mermaid
graph TD
    subgraph "数据采集"
        COLLECT[数据采集器] --> METRICS[性能指标]
        COLLECT --> LOGS[系统日志]
        COLLECT --> EVENTS[业务事件]
    end
    
    subgraph "数据处理"
        METRICS --> ANALYZE[数据分析]
        LOGS --> ANALYZE
        EVENTS --> ANALYZE
        ANALYZE --> AGGREGATE[数据聚合]
        AGGREGATE --> STORE[数据存储]
    end
    
    subgraph "监控告警"
        STORE --> MONITOR[监控检查]
        MONITOR --> THRESHOLD{阈值判断}
        THRESHOLD -->|正常| CONTINUE[继续监控]
        THRESHOLD -->|异常| ALERT[触发告警]
        ALERT --> NOTIFY[发送通知]
        NOTIFY --> ESCALATE[告警升级]
        CONTINUE --> MONITOR
        ESCALATE --> MONITOR
    end
    
    style ANALYZE fill:#e3f2fd
    style ALERT fill:#ffebee
    style NOTIFY fill:#fff3e0
```

### 2. 性能监控指标

```mermaid
mindmap
  root((系统监控))
    业务指标
      订单处理量
      发货成功率
      响应时间
      错误率
    系统指标
      CPU使用率
      内存使用量
      磁盘使用量
      网络流量
    API指标
      API调用次数
      API响应时间
      API错误率
      限流统计
    数据库指标
      连接数
      查询性能
      事务成功率
      锁等待时间
```

---

## 🎯 关键性能指标 (KPI)

### 1. 业务KPI监控

| 指标名称 | 目标值 | 告警阈值 | 监控频率 |
|---------|--------|---------|----------|
| 自动发货成功率 | ≥95% | <90% | 实时 |
| 订单处理延迟 | ≤5分钟 | >10分钟 | 实时 |
| 通知发送成功率 | ≥99% | <95% | 实时 |
| 系统可用性 | ≥99.9% | <99% | 实时 |
| API响应时间 | ≤2秒 | >5秒 | 实时 |

### 2. 技术KPI监控

| 指标名称 | 目标值 | 告警阈值 | 监控频率 |
|---------|--------|---------|----------|
| 内存使用率 | ≤80% | >90% | 每分钟 |
| CPU使用率 | ≤70% | >85% | 每分钟 |
| 磁盘使用率 | ≤80% | >90% | 每小时 |
| 数据库连接数 | ≤50 | >80 | 每分钟 |
| 错误日志数量 | ≤10/小时 | >50/小时 | 每小时 |

---

这个工作流程文档详细描述了系统运行的各个环节，从用户交互到订单处理，从异常处理到性能监控，为理解和维护系统提供了完整的流程指导。