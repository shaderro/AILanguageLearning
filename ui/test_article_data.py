#!/usr/bin/env python3
"""
测试文章数据加载和显示
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from viewmodels.article_list_viewmodel import ArticleListViewModel
    print("✅ 成功导入ArticleListViewModel")
except ImportError as e:
    print(f"❌ 无法导入ArticleListViewModel: {e}")
    sys.exit(1)

def test_article_loading():
    """测试文章数据加载"""
    print("🧪 测试文章数据加载...")
    
    # 创建ViewModel
    viewmodel = ArticleListViewModel()
    
    # 加载文章
    articles = viewmodel.load_articles()
    
    print(f"📚 加载了 {len(articles)} 篇文章:")
    for article in articles:
        print(f"  - ID: {article.text_id}")
        print(f"    标题: {article.title}")
        print(f"    单词数: {article.word_count}")
        print(f"    难度: {article.level}")
        print(f"    进度: {article.progress_percent}%")
        print()
    
    # 测试获取文章详情
    if articles:
        first_article = articles[0]
        print(f"🔍 测试获取文章详情 (ID: {first_article.text_id}):")
        
        article_detail = viewmodel.get_article_by_id(first_article.text_id)
        if article_detail:
            print(f"  ✅ 成功获取文章: {article_detail.text_title}")
            print(f"  📝 句子数量: {len(article_detail.text_by_sentence)}")
            for i, sentence in enumerate(article_detail.text_by_sentence[:3]):  # 只显示前3句
                print(f"    句子 {i+1}: {sentence.sentence_body[:50]}...")
        else:
            print(f"  ❌ 无法获取文章详情")
    
    return articles

if __name__ == "__main__":
    print("🚀 开始测试文章数据...")
    print("-" * 50)
    
    articles = test_article_loading()
    
    print("-" * 50)
    print("✅ 测试完成!") 