#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品提示词配置工具
帮助用户为每个商品设置个性化的销售话术
"""
from product_prompt_manager import ProductPromptManager
from loguru import logger
import json

def interactive_setup():
    """交互式配置商品提示词"""
    print("🎯 商品个性化提示词配置工具")
    print("=" * 50)
    
    manager = ProductPromptManager()
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 为新商品创建个性化提示词")
        print("2. 查看已配置的商品")
        print("3. 删除商品提示词")
        print("4. 创建示例商品提示词")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == "1":
            create_new_product_prompt(manager)
        elif choice == "2":
            list_existing_prompts(manager)
        elif choice == "3":
            delete_product_prompt(manager)
        elif choice == "4":
            create_sample_prompts(manager)
        elif choice == "5":
            print("👋 配置完成，再见！")
            break
        else:
            print("❌ 无效选项，请重新选择")

def create_new_product_prompt(manager):
    """创建新商品的个性化提示词"""
    print("\n🆕 创建新商品个性化提示词")
    print("-" * 30)
    
    # 基本信息
    item_id = input("商品ID (例如: phone_001): ").strip()
    if not item_id:
        print("❌ 商品ID不能为空")
        return
    
    title = input("商品名称: ").strip()
    if not title:
        print("❌ 商品名称不能为空")
        return
    
    desc = input("商品描述: ").strip()
    
    try:
        price = float(input("商品价格 (元): ").strip())
    except ValueError:
        print("❌ 价格格式错误")
        return
    
    # 高级设置
    print("\n🔧 高级设置 (可选，直接回车使用默认值):")
    
    max_discount_input = input("最大折扣比例 (0-1，默认0.5): ").strip()
    max_discount = 0.5
    if max_discount_input:
        try:
            max_discount = min(1.0, max(0, float(max_discount_input)))
        except ValueError:
            pass
    
    selling_points = input("核心卖点 (用逗号分隔): ").strip()
    selling_points_list = [p.strip() for p in selling_points.split(",")] if selling_points else ["质量上乘", "性价比高"]
    
    target_customers = input("目标客户群体 (默认: 有品味的顾客): ").strip()
    if not target_customers:
        target_customers = "有品味的顾客"
    
    urgency_input = input("紧迫感等级 (low/medium/high，默认medium): ").strip().lower()
    urgency_level = urgency_input if urgency_input in ['low', 'medium', 'high'] else 'medium'
    
    # 构建配置
    product_info = {
        'title': title,
        'desc': desc,
        'soldPrice': price
    }
    
    custom_settings = {
        'max_discount': max_discount,
        'selling_points': selling_points_list,
        'target_customers': target_customers,
        'urgency_level': urgency_level
    }
    
    # 创建提示词
    success = manager.create_product_prompt(item_id, product_info, custom_settings)
    
    if success:
        print(f"\n✅ 成功为商品 '{title}' 创建个性化提示词！")
        print(f"📁 商品ID: {item_id}")
        print(f"💰 价格: ¥{price}")
        print(f"📈 最大折扣: {int(max_discount*100)}%")
        print(f"⭐ 卖点: {', '.join(selling_points_list)}")
    else:
        print("❌ 创建失败，请检查输入信息")

def list_existing_prompts(manager):
    """查看已配置的商品"""
    print("\n📋 已配置的商品提示词:")
    print("-" * 40)
    
    products = manager.list_product_prompts()
    
    if not products:
        print("暂无配置的商品提示词")
        return
    
    for i, product in enumerate(products, 1):
        print(f"{i}. {product['title']}")
        print(f"   ID: {product['item_id']}")
        print(f"   价格: ¥{product['price']}")
        print()

def delete_product_prompt(manager):
    """删除商品提示词"""
    print("\n🗑️  删除商品提示词")
    print("-" * 20)
    
    products = manager.list_product_prompts()
    if not products:
        print("暂无可删除的商品提示词")
        return
    
    # 显示商品列表
    for i, product in enumerate(products, 1):
        print(f"{i}. {product['title']} (ID: {product['item_id']})")
    
    try:
        choice = int(input("\n请选择要删除的商品 (输入编号): ").strip())
        if 1 <= choice <= len(products):
            product = products[choice - 1]
            item_id = product['item_id']
            
            confirm = input(f"确认删除 '{product['title']}' 的提示词吗？(y/N): ").strip().lower()
            if confirm == 'y':
                success = manager.delete_product_prompt(item_id)
                if success:
                    print(f"✅ 已删除商品 '{product['title']}' 的提示词")
                else:
                    print("❌ 删除失败")
            else:
                print("取消删除")
        else:
            print("❌ 无效的编号")
    except ValueError:
        print("❌ 请输入有效的数字")

def create_sample_prompts(manager):
    """创建示例商品提示词"""
    print("\n🎯 创建示例商品提示词")
    print("-" * 25)
    
    samples = [
        {
            'item_id': 'iphone_demo_001',
            'info': {
                'title': 'iPhone 15 Pro Max 256GB',
                'desc': '全新未拆封iPhone 15 Pro Max，钛合金材质，A17 Pro芯片，4800万像素三摄',
                'soldPrice': 9999
            },
            'settings': {
                'max_discount': 0.3,
                'selling_points': ['A17 Pro芯片', '钛合金材质', '4800万像素', '256GB存储'],
                'target_customers': '高端科技用户',
                'urgency_level': 'high'
            }
        },
        {
            'item_id': 'laptop_demo_001', 
            'info': {
                'title': 'MacBook Pro 16寸 M3芯片',
                'desc': '苹果MacBook Pro 16英寸，M3芯片，32GB内存，1TB固态硬盘，适合专业人士',
                'soldPrice': 19999
            },
            'settings': {
                'max_discount': 0.25,
                'selling_points': ['M3芯片', '16寸视网膜屏', '32GB内存', '专业级性能'],
                'target_customers': '设计师和开发者',
                'urgency_level': 'medium'
            }
        },
        {
            'item_id': 'headphone_demo_001',
            'info': {
                'title': 'AirPods Pro 2代',
                'desc': 'Apple AirPods Pro 第二代，主动降噪，空间音频，MagSafe充电盒',
                'soldPrice': 1899
            },
            'settings': {
                'max_discount': 0.4,
                'selling_points': ['主动降噪', '空间音频', 'MagSafe充电', 'H2芯片'],
                'target_customers': '音乐爱好者',
                'urgency_level': 'medium'
            }
        }
    ]
    
    success_count = 0
    for sample in samples:
        success = manager.create_product_prompt(
            sample['item_id'], 
            sample['info'], 
            sample['settings']
        )
        if success:
            success_count += 1
            print(f"✅ 创建示例商品: {sample['info']['title']}")
        else:
            print(f"❌ 创建失败: {sample['info']['title']}")
    
    print(f"\n🎉 成功创建 {success_count}/{len(samples)} 个示例商品提示词！")
    print("💡 这些示例展示了如何为不同类型的商品配置个性化话术")

if __name__ == "__main__":
    try:
        interactive_setup()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消，再见！")