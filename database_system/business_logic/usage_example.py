"""
重构后的数据库架构使用示例
"""
from database_manager import DatabaseManager
from business_logic.managers import UnifiedDataManager


def example_usage():
    """使用示例"""
    # 1. 创建数据库管理器（类似原来的 DatabaseManager）
    db_manager = DatabaseManager(environment='development')
    session = db_manager.get_session()
    
    # 2. 创建统一数据管理器
    data_manager = UnifiedDataManager(session)
    
    try:
        # 3. 使用词汇管理器
        print("=== 词汇管理 ===")
        # 添加词汇
        vocab = data_manager.vocab.add_vocab(
            vocab_body="hello", 
            explanation="问候语", 
            source="manual"
        )
        print(f"添加词汇: {vocab.vocab_body}")
        
        # 搜索词汇
        search_results = data_manager.vocab.search_vocabs("hello")
        print(f"搜索结果: {len(search_results)} 个")
        
        # 获取词汇统计
        vocab_stats = data_manager.vocab.get_vocab_stats()
        print(f"词汇统计: {vocab_stats}")
        
        # 4. 使用语法管理器
        print("\n=== 语法管理 ===")
        grammar_rule = data_manager.grammar.add_grammar_rule(
            rule_name="现在时", 
            rule_summary="表示现在发生的动作"
        )
        print(f"添加语法规则: {grammar_rule.rule_name}")
        
        # 5. 使用文章管理器
        print("\n=== 文章管理 ===")
        text = data_manager.text.create_text("示例文章")
        print(f"创建文章: {text.text_title}")
        
        # 添加句子
        sentence = data_manager.text.create_sentence(
            text_id=text.text_id,
            sentence_id=1,
            sentence_body="Hello, world!",
            difficulty_level="easy"
        )
        print(f"添加句子: {sentence.sentence_body}")
        
        # 6. 使用标记管理器
        print("\n=== 标记管理 ===")
        token = data_manager.token.create_token(
            text_id=text.text_id,
            sentence_id=1,
            token_body="Hello",
            token_type="word"
        )
        print(f"创建标记: {token.token_body}")
        
        # 7. 使用已提问标记管理器
        print("\n=== 已提问标记管理 ===")
        asked_token = data_manager.asked_token.mark_token_as_asked(
            user_id="user123",
            text_id=text.text_id,
            sentence_id=1,
            sentence_token_id=token.token_id
        )
        print(f"标记已提问: {asked_token.user_id}")
        
        # 8. 使用统计管理器
        print("\n=== 统计信息 ===")
        comprehensive_stats = data_manager.stats.get_comprehensive_stats()
        print(f"综合统计: {comprehensive_stats}")
        
        # 9. 提交事务
        data_manager.commit()
        print("\n事务提交成功")
        
    except Exception as e:
        print(f"发生错误: {e}")
        data_manager.rollback()
        print("事务已回滚")
    
    finally:
        # 10. 关闭会话
        data_manager.close()
        print("会话已关闭")


def compare_old_vs_new():
    """对比新旧架构"""
    print("=== 架构对比 ===")
    print("旧架构:")
    print("- crud.py: 378行，所有CRUD操作混在一起")
    print("- data_access_layer.py: 86行，简单的DAL封装")
    print("- 职责不清晰，难以维护")
    
    print("\n新架构:")
    print("- crud/: 按功能拆分为6个独立模块")
    print("- managers/: 高级业务逻辑封装")
    print("- data_access_layer.py: 统一管理器模式")
    print("- 职责清晰，易于维护和扩展")
    
    print("\n优势:")
    print("1. 关注点分离: CRUD专注数据库操作，Manager专注业务逻辑")
    print("2. 可维护性: 修改某个功能不影响其他模块")
    print("3. 可测试性: 每个模块可独立测试")
    print("4. 可扩展性: 新增功能只需添加对应模块")
    print("5. 一致性: 统一的管理器模式，使用方式一致")


if __name__ == "__main__":
    compare_old_vs_new()
    print("\n" + "="*50)
    # example_usage()  # 取消注释以运行实际示例
