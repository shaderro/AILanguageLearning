"""
数据绑定服务架构演示
展示通用基类和特定子类的区别和使用方法
"""

import sys
import os
# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_binding_service import DataBindingService
from services.language_learning_binding_service import LanguageLearningBindingService
from viewmodels.text_input_chat_viewmodel import TextInputChatViewModel

def demonstrate_generic_service():
    """演示通用数据绑定服务"""
    print("\n=== 通用数据绑定服务演示 ===")
    
    # 创建通用服务
    generic_service = DataBindingService()
    
    # 创建ViewModel
    viewmodel = TextInputChatViewModel(generic_service)
    
    # 注册ViewModel
    generic_service.register_viewmodel('chat', viewmodel)
    
    # 设置数据绑定
    generic_service.bind_data_to_viewmodel('title', 'chat', 'article_title')
    generic_service.bind_data_to_viewmodel('content', 'chat', 'article_content')
    
    # 更新数据
    generic_service.update_data('title', 'Generic Article Title')
    generic_service.update_data('content', 'This is generic content...')
    
    print("✅ 通用服务：只提供数据绑定功能，不包含业务逻辑")
    print(f"   - 文章标题: {viewmodel.article_title}")
    print(f"   - 文章内容: {viewmodel.article_content[:30]}...")
    
    return generic_service

def demonstrate_language_learning_service():
    """演示语言学习特定的数据绑定服务"""
    print("\n=== 语言学习特定服务演示 ===")
    
    # 创建语言学习特定服务
    language_service = LanguageLearningBindingService()
    
    # 创建ViewModel
    viewmodel = TextInputChatViewModel(language_service)
    
    # 注册ViewModel
    language_service.register_viewmodel('chat', viewmodel)
    
    # 设置数据绑定
    language_service.bind_data_to_viewmodel('title', 'chat', 'article_title')
    language_service.bind_data_to_viewmodel('content', 'chat', 'article_content')
    
    # 使用语言学习特定功能
    article_data = language_service.load_article_data('article_001')
    vocab_data = language_service.get_vocabulary_data('This is a sample text for vocabulary analysis.')
    grammar_data = language_service.get_grammar_rules('The book was written by Shakespeare.')
    difficulty_analysis = language_service.analyze_text_difficulty('This is a sample text for difficulty analysis.')
    
    print("✅ 语言学习服务：继承通用功能 + 添加语言学习特定功能")
    print(f"   - 加载文章: {article_data['title'] if article_data else 'None'}")
    print(f"   - 提取词汇: {len(vocab_data)} 个词汇")
    print(f"   - 语法规则: {len(grammar_data)} 条规则")
    print(f"   - 难度分析: {difficulty_analysis.get('overall_difficulty', 'Unknown')}")
    
    return language_service

def compare_services():
    """比较两种服务的功能"""
    print("\n=== 服务功能对比 ===")
    
    # 通用服务功能
    generic_service = DataBindingService()
    generic_methods = [method for method in dir(generic_service) 
                      if not method.startswith('_') and callable(getattr(generic_service, method))]
    
    # 语言学习服务功能
    language_service = LanguageLearningBindingService()
    language_methods = [method for method in dir(language_service) 
                       if not method.startswith('_') and callable(getattr(language_service, method))]
    
    # 找出语言学习服务特有的方法
    language_specific_methods = [method for method in language_methods 
                               if method not in generic_methods]
    
    print("📋 通用服务功能:")
    for method in sorted(generic_methods):
        print(f"   - {method}")
    
    print("\n📋 语言学习服务特有功能:")
    for method in sorted(language_specific_methods):
        print(f"   - {method}")
    
    print(f"\n📊 统计:")
    print(f"   - 通用服务方法数: {len(generic_methods)}")
    print(f"   - 语言学习服务方法数: {len(language_methods)}")
    print(f"   - 语言学习特有方法数: {len(language_specific_methods)}")

def demonstrate_inheritance_benefits():
    """演示继承架构的优势"""
    print("\n=== 继承架构优势演示 ===")
    
    # 1. 代码复用
    print("🔄 代码复用:")
    print("   - 语言学习服务自动获得所有通用功能")
    print("   - 不需要重新实现数据绑定逻辑")
    
    # 2. 类型安全
    print("\n🛡️ 类型安全:")
    print("   - 两个服务都支持类型注解")
    print("   - IDE可以提供更好的代码提示")
    
    # 3. 易于维护
    print("\n🔧 易于维护:")
    print("   - 修改通用功能只需要改基类")
    print("   - 所有子类自动获得改进")
    
    # 4. 职责分离
    print("\n📋 职责分离:")
    print("   - 通用服务：只负责数据绑定")
    print("   - 语言学习服务：只负责语言学习业务逻辑")
    
    # 5. 易于测试
    print("\n🧪 易于测试:")
    print("   - 可以独立测试通用功能")
    print("   - 可以独立测试语言学习功能")

if __name__ == '__main__':
    print("🚀 数据绑定服务架构演示")
    print("=" * 50)
    
    # 演示通用服务
    generic_service = demonstrate_generic_service()
    
    # 演示语言学习服务
    language_service = demonstrate_language_learning_service()
    
    # 比较功能
    compare_services()
    
    # 演示继承优势
    demonstrate_inheritance_benefits()
    
    print("\n" + "=" * 50)
    print("✅ 演示完成！")
    print("\n💡 关键要点:")
    print("1. 通用服务提供核心数据绑定功能")
    print("2. 语言学习服务继承通用功能并添加特定业务逻辑")
    print("3. 这种架构实现了职责分离和代码复用")
    print("4. 易于维护和扩展") 