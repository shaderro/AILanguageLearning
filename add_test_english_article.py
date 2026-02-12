"""
为 User 2 添加英语测试文章
包含不同类型的语法长难句，用于测试新语法assistant的功能
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(CURRENT_DIR)
BACKEND_DIR = os.path.join(REPO_ROOT, 'backend')
FRONTEND_BACKEND_DIR = os.path.join(REPO_ROOT, 'frontend', 'my-web-ui', 'backend')

for p in [REPO_ROOT, BACKEND_DIR, FRONTEND_BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# 设置环境变量
os.environ['ENV'] = 'development'

from backend.preprocessing.article_processor import process_article
import importlib.util

# 动态导入 import_article_to_database
spec = importlib.util.spec_from_file_location("main", os.path.join(FRONTEND_BACKEND_DIR, "main.py"))
main_module = importlib.util.module_from_spec(spec)
sys.modules["main"] = main_module
spec.loader.exec_module(main_module)
import_article_to_database = main_module.import_article_to_database

# 测试文章内容 - 包含至少10句不同类型的语法长难句
# 包含相同语法（用于测试查重）和不同语法结构
test_article_content = """
The book that I bought yesterday, which was recommended by my professor, has been extremely helpful in understanding complex grammatical structures.

Although she had studied English for many years, she still found it challenging to master the subjunctive mood, which is often considered one of the most difficult aspects of English grammar.

The students who were selected for the advanced program, having demonstrated exceptional ability in both written and spoken English, will be given the opportunity to study abroad next semester.

It is essential that all participants arrive on time, as the workshop will begin promptly at nine o'clock, and late arrivals will not be permitted to enter once the session has started.

The research conducted by the team of linguists, which spanned over a decade and involved thousands of participants from various linguistic backgrounds, has revealed fascinating insights into how language acquisition occurs in different contexts.

Had I known about the complexity of this grammatical structure earlier, I would have dedicated more time to studying it, but now I must work twice as hard to catch up with my classmates.

The professor explained that the passive voice, which is formed by using a form of the verb "to be" followed by the past participle, is particularly useful when the focus is on the action rather than the person performing it.

What makes this sentence structure particularly interesting is that it allows speakers to emphasize different elements of the sentence depending on their communicative intent, thereby providing greater flexibility in expression.

The committee members, having reviewed all the proposals submitted by the candidates, decided that the project which demonstrated the most innovative approach to language learning would receive the full funding.

Despite the fact that many students struggle with understanding relative clauses, especially those that contain multiple levels of subordination, mastering these structures is crucial for achieving fluency in academic English.

The book that I bought yesterday, which was recommended by my professor, contains numerous examples of complex sentence structures that illustrate how different grammatical elements can be combined to create sophisticated and nuanced expressions.

If the weather had been better, we would have gone to the park, but since it was raining heavily, we decided to stay indoors and practice our grammar exercises instead.
"""

def add_test_article():
    """为 User 2 添加测试文章"""
    user_id = 2
    language = "英文"
    title = "English Grammar Test Article - Complex Sentences"
    
    # 生成文章ID
    article_id = int(datetime.now().timestamp())
    
    print(f"📝 开始处理测试文章...")
    print(f"  - 用户ID: {user_id}")
    print(f"  - 语言: {language}")
    print(f"  - 标题: {title}")
    print(f"  - 文章ID: {article_id}")
    print(f"  - 内容长度: {len(test_article_content)} 字符")
    print(f"  - 句子数量: {len([s for s in test_article_content.split('.') if s.strip()])} 句")
    
    # 处理文章
    try:
        result = process_article(test_article_content, article_id, title, language=language)
        print(f"✅ 文章处理成功")
        print(f"  - 总句子数: {result.get('total_sentences', 0)}")
        print(f"  - 总token数: {result.get('total_tokens', 0)}")
        
        # 导入到数据库
        print(f"\n📥 开始导入文章到数据库...")
        import_result = import_article_to_database(result, article_id, user_id, language=language, title=title)
        
        if import_result:
            print(f"✅ 文章导入成功！")
            print(f"  - 文章ID: {article_id}")
            print(f"  - 用户ID: {user_id}")
            print(f"  - 标题: {title}")
            print(f"\n📋 文章包含的语法结构类型：")
            print(f"  1. 定语从句 (Relative Clauses) - 句子 1, 11")
            print(f"  2. 让步状语从句 (Concessive Clauses) - 句子 2, 10")
            print(f"  3. 现在分词短语 (Present Participle Phrases) - 句子 3, 9")
            print(f"  4. 主语从句 (Subject Clauses) - 句子 4")
            print(f"  5. 过去分词短语 (Past Participle Phrases) - 句子 5")
            print(f"  6. 虚拟语气 (Subjunctive Mood) - 句子 6, 12")
            print(f"  7. 宾语从句 (Object Clauses) - 句子 7")
            print(f"  8. 主语从句 + 表语从句 (Subject + Predicative Clauses) - 句子 8")
            print(f"  9. 条件状语从句 (Conditional Clauses) - 句子 12")
            print(f"\n💡 注意：句子 1 和 11 包含相同的语法结构（定语从句），用于测试查重功能")
            return True
        else:
            print(f"❌ 文章导入失败")
            return False
            
    except Exception as e:
        print(f"❌ 处理文章时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_test_article()
    if success:
        print(f"\n✅ 测试文章添加完成！")
    else:
        print(f"\n❌ 测试文章添加失败！")
        sys.exit(1)

