#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动发货功能测试脚本

用于测试和演示自动发货功能的使用
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from delivery_manager import DeliveryManager
from loguru import logger


def test_basic_operations():
    """测试基本操作"""
    print("=" * 60)
    print("测试1: 基本操作 - 创建、读取、更新、删除")
    print("=" * 60)

    # 初始化发货管理器
    dm = DeliveryManager(db_path="data/test_delivery.db")

    # 测试商品ID
    test_item_id = "test_item_12345"

    # 1. 保存配置
    print("\n✅ 测试保存发货配置...")
    config = {
        'delivery_type': 'netdisk',
        'delivery_content': 'https://pan.baidu.com/s/test123456',
        'extraction_code': 'abcd',
        'custom_message': '',
        'is_enabled': True,
        'stock_count': 100
    }
    success = dm.save_delivery_config(test_item_id, config)
    print(f"保存结果: {'成功' if success else '失败'}")

    # 2. 获取配置
    print("\n✅ 测试获取发货配置...")
    saved_config = dm.get_delivery_config(test_item_id)
    if saved_config:
        print(f"商品ID: {saved_config['item_id']}")
        print(f"发货类型: {saved_config['delivery_type']}")
        print(f"发货内容: {saved_config['delivery_content']}")
        print(f"提取码: {saved_config['extraction_code']}")
        print(f"库存: {saved_config['stock_count']}")

    # 3. 更新配置
    print("\n✅ 测试更新发货配置...")
    config['stock_count'] = 50
    dm.save_delivery_config(test_item_id, config)
    updated_config = dm.get_delivery_config(test_item_id)
    print(f"更新后库存: {updated_config['stock_count']}")

    # 4. 列出所有配置
    print("\n✅ 测试列出所有配置...")
    all_configs = dm.list_delivery_configs()
    print(f"配置总数: {len(all_configs)}")

    # 5. 删除配置
    print("\n✅ 测试删除配置...")
    dm.delete_delivery_config(test_item_id)
    deleted_config = dm.get_delivery_config(test_item_id)
    print(f"删除后查询结果: {'已删除' if not deleted_config else '删除失败'}")


def test_delivery_types():
    """测试不同发货类型"""
    print("\n" + "=" * 60)
    print("测试2: 不同发货类型的消息生成")
    print("=" * 60)

    dm = DeliveryManager(db_path="data/test_delivery.db")

    # 测试网盘类型
    print("\n📦 网盘链接类型:")
    netdisk_config = {
        'delivery_type': 'netdisk',
        'delivery_content': 'https://pan.baidu.com/s/test123456',
        'extraction_code': 'abcd',
        'custom_message': ''
    }
    message = dm.build_delivery_message(netdisk_config)
    print(message)

    # 测试卡密类型
    print("\n🎟️ 卡密类型:")
    cardkey_config = {
        'delivery_type': 'cardkey',
        'delivery_content': 'XXXX-XXXX-XXXX-XXXX',
        'custom_message': ''
    }
    message = dm.build_delivery_message(cardkey_config)
    print(message)

    # 测试自定义文本
    print("\n📝 自定义文本类型:")
    text_config = {
        'delivery_type': 'text',
        'delivery_content': '这是一段自定义的发货信息，可以包含任何内容。',
        'custom_message': ''
    }
    message = dm.build_delivery_message(text_config)
    print(message)

    # 测试自定义模板
    print("\n🎨 使用自定义消息模板:")
    custom_template_config = {
        'delivery_type': 'netdisk',
        'delivery_content': 'https://pan.baidu.com/s/test123456',
        'extraction_code': 'abcd',
        'custom_message': '亲爱的客户，您购买的【{title}】已发货！\n\n网盘：{content}\n提取码：{code}\n\n价格：{price}元\n\n感谢支持！'
    }
    item_info = {
        'title': '测试商品',
        'soldPrice': 99.99
    }
    message = dm.build_delivery_message(custom_template_config, item_info)
    print(message)


def test_stock_management():
    """测试库存管理"""
    print("\n" + "=" * 60)
    print("测试3: 库存管理")
    print("=" * 60)

    dm = DeliveryManager(db_path="data/test_delivery.db")
    test_item_id = "stock_test_item"

    # 设置有限库存
    print("\n✅ 设置库存为10...")
    config = {
        'delivery_type': 'netdisk',
        'delivery_content': 'https://pan.baidu.com/s/test',
        'extraction_code': 'test',
        'is_enabled': True,
        'stock_count': 10
    }
    dm.save_delivery_config(test_item_id, config)

    # 检查库存
    print(f"当前库存: {dm.get_delivery_config(test_item_id)['stock_count']}")
    print(f"库存充足: {dm.check_stock(test_item_id)}")

    # 减少库存
    print("\n✅ 模拟3次发货...")
    for i in range(3):
        dm.decrease_stock(test_item_id, 1)
        current_stock = dm.get_delivery_config(test_item_id)['stock_count']
        print(f"第{i+1}次发货后库存: {current_stock}")

    # 测试无限库存
    print("\n✅ 设置无限库存（-1）...")
    config['stock_count'] = -1
    dm.save_delivery_config(test_item_id, config)
    print(f"库存设置为: {dm.get_delivery_config(test_item_id)['stock_count']}")
    print(f"库存充足: {dm.check_stock(test_item_id)}")

    # 清理测试数据
    dm.delete_delivery_config(test_item_id)


def test_delivery_records():
    """测试发货记录"""
    print("\n" + "=" * 60)
    print("测试4: 发货记录管理")
    print("=" * 60)

    dm = DeliveryManager(db_path="data/test_delivery.db")

    # 记录几次发货
    print("\n✅ 记录3次发货...")
    for i in range(3):
        record = {
            'order_id': f'order_{i+1}',
            'item_id': 'test_item_123',
            'buyer_id': f'buyer_{i+1}',
            'chat_id': f'chat_{i+1}',
            'delivery_type': 'netdisk',
            'delivery_content': 'https://pan.baidu.com/s/test',
            'status': 'success' if i < 2 else 'failed',
            'error_message': '' if i < 2 else '库存不足'
        }
        dm.record_delivery(record)
        print(f"记录发货 #{i+1}: {record['status']}")

    # 查询发货记录
    print("\n✅ 查询发货记录...")
    records = dm.get_delivery_records(limit=10)
    print(f"总记录数: {len(records)}")
    for record in records[:3]:
        print(f"- 商品: {record['item_id']}, 买家: {record['buyer_id']}, 状态: {record['status']}")

    # 获取统计信息
    print("\n✅ 获取统计信息...")
    stats = dm.get_delivery_stats()
    print(f"总配置数: {stats['total_configs']}")
    print(f"已启用配置: {stats['enabled_configs']}")
    print(f"总发货次数: {stats['total_deliveries']}")
    print(f"成功发货次数: {stats['success_deliveries']}")
    print(f"成功率: {stats['success_rate']}%")


def test_complete_workflow():
    """测试完整工作流程"""
    print("\n" + "=" * 60)
    print("测试5: 完整发货流程模拟")
    print("=" * 60)

    dm = DeliveryManager(db_path="data/test_delivery.db")

    # 场景：卖家配置了一个虚拟商品的自动发货
    item_id = "virtual_product_001"
    buyer_id = "buyer_12345"
    chat_id = "chat_67890"

    print("\n步骤1: 配置商品发货信息")
    config = {
        'delivery_type': 'netdisk',
        'delivery_content': 'https://pan.baidu.com/s/example123',
        'extraction_code': 'wxyz',
        'custom_message': '',
        'is_enabled': True,
        'stock_count': 5
    }
    dm.save_delivery_config(item_id, config)
    print("✅ 配置完成")

    print("\n步骤2: 买家付款，触发自动发货")
    print("📦 检查是否配置了自动发货...")
    delivery_config = dm.get_delivery_config(item_id)
    if delivery_config and delivery_config.get('is_enabled'):
        print("✅ 已配置自动发货")

        print("\n步骤3: 检查库存")
        if dm.check_stock(item_id):
            print("✅ 库存充足")

            print("\n步骤4: 生成发货消息")
            item_info = {'title': '测试虚拟商品', 'soldPrice': 19.9}
            message = dm.build_delivery_message(delivery_config, item_info)
            print(f"发货消息:\n{message}")

            print("\n步骤5: 发送消息给买家（模拟）")
            print("✅ 消息已发送")

            print("\n步骤6: 记录发货")
            dm.record_delivery({
                'item_id': item_id,
                'buyer_id': buyer_id,
                'chat_id': chat_id,
                'delivery_type': delivery_config['delivery_type'],
                'delivery_content': delivery_config['delivery_content'],
                'status': 'success'
            })
            print("✅ 发货记录已保存")

            print("\n步骤7: 减少库存")
            dm.decrease_stock(item_id, 1)
            new_stock = dm.get_delivery_config(item_id)['stock_count']
            print(f"✅ 库存已更新: {new_stock}")

            print("\n🎉 发货流程完成！")

    # 清理测试数据
    dm.delete_delivery_config(item_id)


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "自动发货功能测试" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")

    try:
        # 运行所有测试
        test_basic_operations()
        test_delivery_types()
        test_stock_management()
        test_delivery_records()
        test_complete_workflow()

        print("\n")
        print("=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        print("\n💡 提示:")
        print("- 测试数据库文件: data/test_delivery.db")
        print("- 生产数据库文件: data/delivery.db")
        print("- 更多信息请查看: docs/AUTO_DELIVERY.md")
        print()

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
