#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试豆包AI连接
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

def test_doubao_connection():
    """测试豆包AI连接"""
    print("🧪 测试豆包AI连接...")
    
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    api_key = os.getenv("ARK_API_KEY") or os.getenv("API_KEY")
    base_url = os.getenv("MODEL_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    
    print(f"📋 配置信息:")
    print(f"   API_KEY: {api_key[:10] if api_key else '未设置'}...")
    print(f"   BASE_URL: {base_url}")
    print(f"   MODEL: {model_name}")
    
    if not api_key:
        print("❌ 错误: 请在.env文件中设置ARK_API_KEY")
        print("\n💡 解决方法:")
        print("1. 获取豆包AI的API Key")
        print("2. 在.env文件中设置: ARK_API_KEY=your_actual_api_key")
        return
    
    try:
        # 初始化客户端
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        
        print("\n🚀 发送测试请求...")
        
        # 发送简单测试请求
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user", 
                    "content": "你好，请简单介绍一下你自己"
                }
            ],
            max_tokens=50
        )
        
        print("✅ 连接成功!")
        print(f"📤 测试回复: {response.choices[0].message.content}")
        print("\n🎉 豆包AI配置完成，可以正常使用XianyuAutoAgent了！")
        
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        print("\n🛠️ 常见问题排查:")
        print("1. 检查API Key是否正确")
        print("2. 确认网络连接正常")
        print("3. 验证模型名称是否正确")
        print("4. 检查API服务是否可用")

if __name__ == "__main__":
    test_doubao_connection()