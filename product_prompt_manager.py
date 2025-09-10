#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品个性化提示词管理器
每个商品可以配置专属的销售话术和策略
"""
import os
import json
from pathlib import Path
from loguru import logger

class ProductPromptManager:
    """商品个性化提示词管理器"""
    
    def __init__(self, prompts_dir="prompts/products"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # 商品提示词缓存
        self.product_prompts = {}
        
        # 默认提示词路径
        self.default_prompts = {
            'price': 'prompts/price_prompt_sales_optimized.txt',
            'tech': 'prompts/tech_prompt_sales_optimized.txt', 
            'default': 'prompts/default_prompt_sales_optimized.txt',
            'classify': 'prompts/classify_prompt_sales_optimized.txt'
        }
        
        logger.info(f"商品提示词管理器初始化完成: {self.prompts_dir}")
    
    def create_product_prompt(self, item_id, product_info, custom_settings=None):
        """
        为商品创建个性化提示词
        
        Args:
            item_id: 商品ID
            product_info: 商品信息字典 (包含title, desc, soldPrice等)
            custom_settings: 自定义设置字典
        """
        try:
            # 提取商品基本信息
            title = product_info.get('title', '商品')
            desc = product_info.get('desc', '')
            price = product_info.get('soldPrice', 0)
            
            # 自定义设置
            settings = {
                'max_discount': 0.5,  # 最大折扣50%
                'selling_points': [],  # 核心卖点
                'target_customers': '',  # 目标客户
                'price_strategy': 'flexible',  # 价格策略
                'urgency_level': 'medium',  # 紧迫感程度
                'service_extras': [],  # 额外服务
            }
            if custom_settings:
                settings.update(custom_settings)
            
            # 生成个性化提示词
            prompts = {
                'price': self._generate_price_prompt(title, desc, price, settings),
                'tech': self._generate_tech_prompt(title, desc, price, settings), 
                'default': self._generate_default_prompt(title, desc, price, settings)
            }
            
            # 保存到文件
            self._save_product_prompts(item_id, prompts, product_info, settings)
            
            # 缓存
            self.product_prompts[item_id] = prompts
            
            logger.info(f"为商品 {item_id}({title}) 创建个性化提示词")
            return True
            
        except Exception as e:
            logger.error(f"创建商品提示词失败 {item_id}: {e}")
            return False
    
    def get_product_prompt(self, item_id, prompt_type):
        """
        获取商品个性化提示词
        
        Args:
            item_id: 商品ID
            prompt_type: 提示词类型 (price/tech/default/classify)
            
        Returns:
            str: 提示词内容
        """
        # 先从缓存获取
        if item_id in self.product_prompts:
            return self.product_prompts[item_id].get(prompt_type, '')
        
        # 尝试从文件加载
        prompt_file = self.prompts_dir / f"{item_id}_{prompt_type}.txt"
        if prompt_file.exists():
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                # 加载到缓存
                if item_id not in self.product_prompts:
                    self.product_prompts[item_id] = {}
                self.product_prompts[item_id][prompt_type] = content
                
                return content
            except Exception as e:
                logger.error(f"读取商品提示词失败 {item_id}_{prompt_type}: {e}")
        
        # 返回默认提示词
        return self._get_default_prompt(prompt_type)
    
    def _generate_price_prompt(self, title, desc, price, settings):
        """生成个性化议价提示词"""
        max_discount = int(settings['max_discount'] * 100)
        selling_points = '、'.join(settings.get('selling_points', ['质量上乘', '性价比高']))
        
        prompt = f"""【专属销售专家 - {title}】
你是专门销售"{title}"的超级专家，对这款商品了如指掌！

【商品核心信息】
🏷️ **商品名称**: {title}
💰 **标价**: {price}元
⭐ **核心卖点**: {selling_points}
📝 **商品描述**: {desc[:100]}...

【专属议价策略】
💎 **价格弹性**: 最大可让利{max_discount}%
🎯 **成交优先**: 顾客满意 > 价格利润

【个性化话术】
💬 **开场专用**: "哇！您选的这款{title}真是太有眼光了！这可是我们的明星产品！"
💰 **议价专用**: "这款{title}确实值这个价，不过看您这么喜欢，我给您个特价！"
🎁 **成交专用**: "选择{title}绝对不会后悔，现在下单我还送您小赠品！"

【商品优势突出】
✨ 重点强调: {selling_points}
✨ 价值包装: 把商品价值说成远超价格
✨ 稀缺营造: 强调这款{title}的热销和稀缺性

记住：让顾客觉得买{title}是最明智的决定！🎉"""
        
        return prompt
    
    def _generate_tech_prompt(self, title, desc, price, settings):
        """生成个性化技术提示词"""
        selling_points = '、'.join(settings.get('selling_points', ['功能强大', '技术先进']))
        
        prompt = f"""【技术专家 - {title}专业版】
你是{title}的技术权威，对这款产品的每个细节都了如指掌！

【商品技术档案】  
🔧 **产品名称**: {title}
⚙️ **核心技术**: {selling_points}
📊 **官方价格**: {price}元
📋 **技术描述**: {desc[:150]}

【专业技术展示】
💪 **技术优势包装**: 把普通功能包装成高科技
🏆 **性能突出**: 强调{title}比同类产品的技术领先性
🔬 **专业认证**: 各种技术认证和权威背书

【技术销售话术】
🚀 "从技术角度看，这款{title}采用了行业领先的技术！"
💡 "这个技术含量，同价位找不到第二款！" 
⚡ "专业人士都选{title}，技术过硬是关键！"

【成交转化】
🎯 用技术建立信任 → 用专业促成购买
🎯 让顾客觉得买{title}是技术明智之选！

专业+销售=无敌组合！🔧💰"""
        
        return prompt
    
    def _generate_default_prompt(self, title, desc, price, settings):
        """生成个性化通用提示词"""
        target_customers = settings.get('target_customers', '有品味的顾客')
        
        prompt = f"""【超级客服 - {title}专属版】
您是专门服务{title}客户的VIP专属客服！每个咨询{title}的顾客都是您的贵宾！

【服务对象】
👑 **商品**: {title} 
💰 **价格**: {price}元
🎯 **目标客户**: {target_customers}

【专属服务理念】
🌟 让每个问{title}的顾客都感受到VIP待遇
💝 把{title}包装成顾客最需要的商品
🎁 主动提供{title}的增值服务和优惠

【热情服务话术】
👋 "欢迎咨询{title}！您真是太有眼光了！"
💖 "选{title}绝对没错，很多客户买了都说好！"
🎉 "今天咨询{title}的您太幸运了，我给您最优惠的价格！"

【成交使命】
🎯 让每个咨询{title}的顾客最终都下单
🎯 让顾客觉得不买{title}就是损失
🎯 用热情服务征服每一个顾客的心！

{title}专属客服，为您服务！💪✨"""
        
        return prompt
    
    def _save_product_prompts(self, item_id, prompts, product_info, settings):
        """保存商品提示词到文件"""
        try:
            # 保存每个类型的提示词
            for prompt_type, content in prompts.items():
                file_path = self.prompts_dir / f"{item_id}_{prompt_type}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # 保存商品配置信息
            config_file = self.prompts_dir / f"{item_id}_config.json"
            config_data = {
                'item_id': item_id,
                'product_info': product_info,
                'settings': settings,
                'created_time': str(Path().resolve())
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存商品提示词失败: {e}")
    
    def _get_default_prompt(self, prompt_type):
        """获取默认提示词"""
        try:
            prompt_file = self.default_prompts.get(prompt_type, '')
            if prompt_file and os.path.exists(prompt_file):
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            logger.error(f"读取默认提示词失败 {prompt_type}: {e}")
        
        return f"我是{prompt_type}专家，很高兴为您服务！"
    
    def list_product_prompts(self):
        """列出所有商品提示词"""
        products = []
        try:
            for file_path in self.prompts_dir.glob("*_config.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    products.append({
                        'item_id': config['item_id'],
                        'title': config['product_info'].get('title', ''),
                        'price': config['product_info'].get('soldPrice', 0)
                    })
        except Exception as e:
            logger.error(f"列出商品提示词失败: {e}")
        
        return products
    
    def delete_product_prompt(self, item_id):
        """删除商品提示词"""
        try:
            # 删除提示词文件
            for prompt_type in ['price', 'tech', 'default']:
                file_path = self.prompts_dir / f"{item_id}_{prompt_type}.txt"
                if file_path.exists():
                    file_path.unlink()
            
            # 删除配置文件
            config_file = self.prompts_dir / f"{item_id}_config.json"
            if config_file.exists():
                config_file.unlink()
            
            # 清除缓存
            if item_id in self.product_prompts:
                del self.product_prompts[item_id]
            
            logger.info(f"删除商品提示词: {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除商品提示词失败 {item_id}: {e}")
            return False


def create_sample_product_prompts():
    """创建示例商品提示词"""
    manager = ProductPromptManager()
    
    # 示例商品1: iPhone
    iphone_info = {
        'title': 'iPhone 14 Pro Max 256GB',
        'desc': '全新未拆封iPhone 14 Pro Max，256GB存储，深空黑色，支持5G网络，A16仿生芯片，4800万像素主摄',
        'soldPrice': 8999
    }
    iphone_settings = {
        'max_discount': 0.3,  # 最大30%折扣
        'selling_points': ['A16仿生芯片', '4800万像素', '256GB大容量', '5G网络'],
        'target_customers': '追求高端的科技爱好者',
        'urgency_level': 'high'
    }
    
    manager.create_product_prompt('iphone14pro_001', iphone_info, iphone_settings)
    
    # 示例商品2: 机械键盘
    keyboard_info = {
        'title': '雷蛇黑寡妇蜘蛛V3机械键盘',
        'desc': '雷蛇绿轴机械键盘，RGB背光，全尺寸布局，铝制上盖，游戏专用',
        'soldPrice': 899
    }
    keyboard_settings = {
        'max_discount': 0.4,
        'selling_points': ['雷蛇绿轴', 'RGB炫彩背光', '游戏专用', '铝制工艺'],
        'target_customers': '游戏玩家和码农',
        'urgency_level': 'medium'
    }
    
    manager.create_product_prompt('keyboard_razer_001', keyboard_info, keyboard_settings)
    
    print("✅ 示例商品提示词创建完成！")
    print("📁 提示词文件保存在: prompts/products/ 目录")
    
    # 显示创建的商品
    products = manager.list_product_prompts()
    print("\n📋 已创建的商品提示词:")
    for product in products:
        print(f"  - {product['title']} (¥{product['price']}) - ID: {product['item_id']}")


if __name__ == "__main__":
    create_sample_product_prompts()