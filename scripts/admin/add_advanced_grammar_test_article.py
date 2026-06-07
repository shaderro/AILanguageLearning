#!/usr/bin/env python3
"""
添加高级语法测试文章
包含10个不同语法知识点的长难句
"""
import sys
import os
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# 添加项目路径
BACKEND_DIR = os.path.join(REPO_ROOT, 'backend')
FRONTEND_BACKEND_DIR = os.path.join(REPO_ROOT, 'frontend', 'my-web-ui', 'backend')

for p in [REPO_ROOT, BACKEND_DIR, FRONTEND_BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# 设置环境变量
os.environ['ENV'] = 'development'

# 动态导入必要的模块
from backend.preprocessing.article_processor import process_article
from database_system.database_manager import DatabaseManager
from backend.data_managers import OriginalTextManagerDB
from database_system.business_logic.models import OriginalText, Sentence, Token, WordToken, User
from database_system.business_logic.crud import TokenCRUD

# 测试文章内容 - 包含10个不同语法知识点的长难句
test_article_content = """
Advanced English Grammar Structures: A Comprehensive Study

1. The scientist who discovered the revolutionary treatment, which has saved countless lives since its introduction in 2020, was awarded the Nobel Prize in Medicine, demonstrating how persistence and innovation can transform medical science.

2. Although the economic forecast appears bleak, with unemployment rates rising and inflation reaching unprecedented levels, many economists believe that implementing strategic fiscal policies could potentially stabilize the market within the next two years.

3. Having completed her doctoral thesis on quantum mechanics, which took her nearly five years of intensive research, Dr. Sarah Chen decided to pursue a postdoctoral position at MIT, where she could further explore the applications of quantum computing in artificial intelligence.

4. Were it not for the timely intervention of the international community, the humanitarian crisis in the region would have escalated beyond control, leaving millions of people without access to basic necessities such as food, water, and medical care.

5. Not only did the archaeological team uncover ancient artifacts dating back to the Bronze Age, but they also discovered a previously unknown civilization that had developed sophisticated irrigation systems, challenging our understanding of early human settlements.

6. It was through years of meticulous observation and data collection that the research team finally identified the correlation between climate patterns and migratory bird behavior, a discovery that has profound implications for conservation efforts worldwide.

7. The company's decision to restructure its operations, while maintaining its commitment to environmental sustainability, reflects a strategic shift towards renewable energy sources, a move that industry analysts predict will position it as a market leader in the coming decade.

8. The ancient manuscript, its pages yellowed with age and its binding fragile, revealed secrets about the lost civilization that had been hidden for centuries, providing historians with invaluable insights into the cultural practices and social structures of that era.

9. The hypothesis that dark matter constitutes approximately 85% of the universe's total mass, though it cannot be directly observed, has gained widespread acceptance among physicists, who continue to search for experimental evidence to support this groundbreaking theory.

10. The more complex the problem becomes, the more essential it is to approach it systematically, breaking it down into manageable components and analyzing each part carefully before attempting to synthesize a comprehensive solution.
"""

def add_test_article():
    """添加测试文章到数据库"""
    user_id = 2  # User 2
    language = "英文"
    title = "Advanced English Grammar Structures: A Comprehensive Study"
    article_id = int(datetime.now().timestamp())
    
    print(f"\n{'='*60}")
    print(f"📝 添加高级语法测试文章")
    print(f"{'='*60}")
    print(f"文章ID: {article_id}")
    print(f"用户ID: {user_id}")
    print(f"语言: {language}")
    print(f"标题: {title}")
    print(f"\n文章内容预览（前200字符）:")
    print(test_article_content[:200] + "...")
    
    try:
        # 处理文章
        print(f"\n🔄 处理文章...")
        result = process_article(test_article_content, article_id)
        
        if not result:
            print("❌ 文章处理失败")
            return False
        
        print(f"✅ 文章处理成功")
        print(f"   - 句子数量: {len(result.get('sentences', []))}")
        
        # 导入到数据库
        print(f"\n💾 导入文章到数据库...")
        
        # 使用数据库管理器直接导入
        db_manager = DatabaseManager(os.environ.get('ENV', 'development'))
        session = db_manager.get_session()
        
        try:
            # 验证用户是否存在
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                print(f"❌ [Import] 用户 {user_id} 不存在")
                return False
            
            text_manager = OriginalTextManagerDB(session)
            token_crud = TokenCRUD(session)
            
            # 1. 创建或更新文章
            text_model = session.query(OriginalText).filter(
                OriginalText.text_id == article_id,
                OriginalText.user_id == user_id
            ).first()
            
            if text_model:
                # 更新现有文章
                text_model.text_title = title
                text_model.language = language
                text_model.processing_status = 'completed'
                print(f"✅ 更新现有文章: {article_id}")
            else:
                # 创建新文章
                text_model = OriginalText(
                    text_id=article_id,
                    user_id=user_id,
                    text_title=title,
                    language=language,
                    processing_status='completed'
                )
                session.add(text_model)
                print(f"✅ 创建新文章: {article_id}")
            
            session.commit()
            
            # 2. 删除旧句子（如果存在）
            session.query(Sentence).filter(
                Sentence.text_id == article_id
            ).delete()
            session.query(Token).filter(
                Token.text_id == article_id
            ).delete()
            session.query(WordToken).filter(
                WordToken.text_id == article_id
            ).delete()
            session.commit()
            
            # 3. 添加句子和tokens
            sentences = result.get('sentences', [])
            for sentence_data in sentences:
                sentence_id = sentence_data.get('sentence_id', 0)
                sentence_body = sentence_data.get('sentence_body', '')
                
                sentence_model = Sentence(
                    sentence_id=sentence_id,
                    text_id=article_id,
                    sentence_body=sentence_body,
                    sentence_difficulty_level=None,
                    grammar_annotations=None,
                    vocab_annotations=None
                )
                session.add(sentence_model)
                
                # 添加tokens
                tokens = sentence_data.get('tokens', [])
                for token_data in tokens:
                    token_model = Token(
                        text_id=article_id,
                        sentence_id=sentence_id,
                        token_body=token_data.get('token_body', ''),
                        token_type=token_data.get('token_type', 'text'),
                        difficulty_level=None,
                        global_token_id=token_data.get('global_token_id'),
                        sentence_token_id=token_data.get('sentence_token_id'),
                        pos_tag=token_data.get('pos_tag'),
                        lemma=token_data.get('lemma'),
                        is_grammar_marker=False,
                        linked_vocab_id=None
                    )
                    session.add(token_model)
            
            session.commit()
            print(f"✅ 成功导入 {len(sentences)} 个句子")
            import_result = True
        except Exception as e:
            session.rollback()
            print(f"❌ 数据库导入失败: {e}")
            import traceback
            traceback.print_exc()
            import_result = False
        finally:
            session.close()
        
        if import_result:
            print(f"✅ 文章导入成功！")
            print(f"\n📊 文章统计:")
            print(f"   - 文章ID: {article_id}")
            print(f"   - 标题: {title}")
            print(f"   - 句子数量: {len(result.get('sentences', []))}")
            print(f"\n📚 包含的语法知识点:")
            print(f"   1. 定语从句 (Relative Clauses) - 句子1")
            print(f"   2. 状语从句 (Adverbial Clauses) - 句子2")
            print(f"   3. 非谓语动词 (Non-finite Verbs) - 句子3")
            print(f"   4. 虚拟语气 (Subjunctive Mood) - 句子4")
            print(f"   5. 倒装句 (Inversion) - 句子5")
            print(f"   6. 强调句 (Emphatic Structures) - 句子6")
            print(f"   7. 主从复合句 (Complex Sentences) - 句子7")
            print(f"   8. 独立主格结构 (Absolute Construction) - 句子8")
            print(f"   9. 同位语从句 (Appositive Clauses) - 句子9")
            print(f"   10. 比较结构 (Comparative Structures) - 句子10")
            return True
        else:
            print("❌ 文章导入失败")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        print("🚀 开始执行脚本...")
        success = add_test_article()
        if success:
            print(f"\n{'='*60}")
            print(f"✅ 测试文章添加完成！")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"❌ 测试文章添加失败！")
            print(f"{'='*60}")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 脚本执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

