# 🤖 豆包AI配置指南

## 📋 配置步骤

### 1. 获取豆包AI API Key
1. 访问 [豆包大模型](https://console.volcengine.com/ark/)
2. 注册/登录账号
3. 创建推理接入点
4. 获取您的 API Key

### 2. 修改环境变量
编辑 `.env` 文件，设置您的API Key：

```env
# 豆包AI配置 - 请替换为您的真实API Key
ARK_API_KEY=your_actual_api_key_here
API_KEY=${ARK_API_KEY}

# 豆包AI模型配置
MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
MODEL_NAME=doubao-seed-1-6-250615
```

### 3. 测试连接
运行测试脚本验证配置：

```bash
python3 test_doubao.py
```

看到 `✅ 连接成功!` 说明配置正确。

### 4. 启动程序
```bash
python3 main.py
```

## 🔧 模型配置说明

### 可用模型列表
根据您的推理接入点，可以使用以下模型：

- `doubao-seed-1-6-250615` - 轻量版本，响应快速
- `doubao-pro-4k` - 专业版本，能力更强
- `doubao-lite-4k` - 轻量版本，性价比高

### 自定义配置
在 `.env` 文件中修改：

```env
# 切换模型
MODEL_NAME=doubao-pro-4k

# 修改地域（如需要）
MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 调整人工接管关键词
TOGGLE_KEYWORDS=人工,转人工
```

## 🚨 常见问题

### Q: 出现 "Connection error" 怎么办？
A: 请检查：
1. API Key是否正确
2. 网络连接是否正常  
3. 模型名称是否与您的接入点匹配
4. 运行 `python3 test_doubao.py` 进行诊断

### Q: 如何切换其他AI服务？
A: 修改 `.env` 中的配置：

```env
# 切换到OpenAI
MODEL_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo
API_KEY=your_openai_api_key

# 切换到阿里云通义千问
MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-max
API_KEY=your_dashscope_api_key
```

### Q: 如何优化回复质量？
A: 您可以：
1. 使用更强的模型（如 doubao-pro-4k）
2. 调整 prompts/ 目录下的提示词文件
3. 根据业务需求修改专家代理的配置

## 🎯 完成配置

配置完成后，您的XianyuAutoAgent将使用豆包AI提供智能客服服务：

- ✅ 智能意图识别
- ✅ 专业技术解答  
- ✅ 灵活议价策略
- ✅ 贴心客户服务

祝您使用愉快！ 🎉