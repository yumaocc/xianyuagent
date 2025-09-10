#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼商品一键发布工具
使用方法:
    python3 publish_tool.py --help
"""

import argparse
import sys
import os
from dotenv import load_dotenv
from loguru import logger
from XianyuApis import XianyuApis
from product_publisher import XianyuProductPublisher, ProductTemplateConfig
from utils.xianyu_utils import trans_cookies


def setup_logger():
    """设置日志"""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )


def init_publisher():
    """初始化发布器"""
    load_dotenv()
    
    cookies_str = os.getenv("COOKIES_STR")
    if not cookies_str:
        logger.error("请在.env文件中配置COOKIES_STR")
        sys.exit(1)
    
    # 初始化API
    xianyu_apis = XianyuApis()
    cookies = trans_cookies(cookies_str)
    xianyu_apis.session.cookies.update(cookies)
    
    # 初始化发布器
    publisher = XianyuProductPublisher(xianyu_apis)
    
    return publisher


def create_template(args):
    """创建商品模板"""
    publisher = init_publisher()
    
    if args.type == 'digital':
        template_data = ProductTemplateConfig.create_digital_product_template()
    elif args.type == 'electronics':
        template_data = ProductTemplateConfig.create_electronics_template()
    else:
        logger.error("不支持的模板类型")
        return
    
    # 更新模板数据
    if args.title:
        template_data['title'] = args.title
    if args.price:
        template_data['price'] = float(args.price)
    if args.description:
        template_data['description'] = args.description
    
    success = publisher.save_template(args.name, template_data)
    if success:
        logger.info(f"✅ 模板创建成功: {args.name}")
    else:
        logger.error("❌ 模板创建失败")


def list_templates(args):
    """列出所有模板"""
    publisher = init_publisher()
    templates = publisher.list_templates()
    
    if not templates:
        logger.info("📋 暂无模板")
        return
    
    logger.info(f"📋 共有 {len(templates)} 个模板:")
    print("\n" + "="*80)
    print(f"{'序号':<4} {'模板名称':<20} {'标题':<30} {'价格':<10} {'自动发布':<8}")
    print("="*80)
    
    for i, template in enumerate(templates, 1):
        auto_publish = "是" if template['auto_publish'] else "否"
        print(f"{i:<4} {template['template_name']:<20} {template['title']:<30} {template['price']:<10} {auto_publish:<8}")
    
    print("="*80 + "\n")


def publish_product(args):
    """发布商品"""
    publisher = init_publisher()
    
    logger.info(f"🚀 开始发布商品: {args.template}")
    
    # 自定义数据
    custom_data = {}
    if args.title:
        custom_data['title'] = args.title
    if args.price:
        custom_data['price'] = float(args.price)
    
    item_id = publisher.publish_product(args.template, custom_data)
    
    if item_id:
        logger.info(f"✅ 商品发布成功!")
        logger.info(f"📦 商品ID: {item_id}")
        logger.info(f"🔗 商品链接: https://www.goofish.com/item?id={item_id}")
    else:
        logger.error("❌ 商品发布失败")


def batch_publish(args):
    """批量发布"""
    publisher = init_publisher()
    
    template_names = args.templates.split(',')
    logger.info(f"🚀 开始批量发布 {len(template_names)} 个商品")
    
    results = publisher.batch_publish(template_names, args.interval)
    
    logger.info("📊 批量发布结果:")
    print("\n" + "="*60)
    print(f"{'模板名称':<25} {'发布结果':<25}")
    print("="*60)
    
    success_count = 0
    for template_name, result in results.items():
        if result != "发布失败":
            success_count += 1
            print(f"{template_name:<25} ✅ 成功 (ID: {result})")
        else:
            print(f"{template_name:<25} ❌ 失败")
    
    print("="*60)
    logger.info(f"📈 成功发布: {success_count}/{len(template_names)}")


def show_records(args):
    """显示发布记录"""
    publisher = init_publisher()
    records = publisher.get_publish_records(args.limit)
    
    if not records:
        logger.info("📋 暂无发布记录")
        return
    
    logger.info(f"📋 最近 {len(records)} 条发布记录:")
    print("\n" + "="*100)
    print(f"{'时间':<20} {'模板名称':<20} {'商品标题':<25} {'状态':<8} {'商品ID':<15}")
    print("="*100)
    
    for record in records:
        status = "✅ 成功" if record['status'] == 'success' else "❌ 失败"
        item_id = record['item_id'] or "N/A"
        publish_time = record['publish_time'][:19] if record['publish_time'] else "N/A"
        
        print(f"{publish_time:<20} {record['template_name'] or 'N/A':<20} {record['title'] or 'N/A':<25} {status:<8} {item_id:<15}")
    
    print("="*100 + "\n")


def main():
    """主函数"""
    setup_logger()
    
    parser = argparse.ArgumentParser(description='闲鱼商品一键发布工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建模板命令
    create_parser = subparsers.add_parser('create', help='创建商品模板')
    create_parser.add_argument('name', help='模板名称')
    create_parser.add_argument('--type', choices=['digital', 'electronics'], 
                              default='digital', help='模板类型')
    create_parser.add_argument('--title', help='商品标题')
    create_parser.add_argument('--price', help='商品价格')
    create_parser.add_argument('--description', help='商品描述')
    create_parser.set_defaults(func=create_template)
    
    # 列出模板命令
    list_parser = subparsers.add_parser('list', help='列出所有模板')
    list_parser.set_defaults(func=list_templates)
    
    # 发布商品命令
    publish_parser = subparsers.add_parser('publish', help='发布商品')
    publish_parser.add_argument('template', help='模板名称')
    publish_parser.add_argument('--title', help='自定义标题')
    publish_parser.add_argument('--price', help='自定义价格')
    publish_parser.set_defaults(func=publish_product)
    
    # 批量发布命令
    batch_parser = subparsers.add_parser('batch', help='批量发布商品')
    batch_parser.add_argument('templates', help='模板名称列表（用逗号分隔）')
    batch_parser.add_argument('--interval', type=int, default=30, help='发布间隔（秒）')
    batch_parser.set_defaults(func=batch_publish)
    
    # 查看记录命令
    records_parser = subparsers.add_parser('records', help='查看发布记录')
    records_parser.add_argument('--limit', type=int, default=20, help='显示记录数量')
    records_parser.set_defaults(func=show_records)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        logger.info("👋 操作已取消")
    except Exception as e:
        logger.error(f"❌ 操作失败: {e}")


if __name__ == '__main__':
    main()