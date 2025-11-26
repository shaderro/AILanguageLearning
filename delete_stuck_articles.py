"""
删除 user 2 中所有状态为"处理中"的文章
"""
from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import OriginalText

def delete_stuck_articles():
    """删除 user 2 中所有状态为'processing'的文章"""
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    try:
        # 查询 user 2 中所有状态为'processing'的文章
        stuck_articles = session.query(OriginalText).filter(
            OriginalText.user_id == 2,
            OriginalText.processing_status == 'processing'
        ).all()
        
        if not stuck_articles:
            print("✅ 没有找到状态为'processing'的文章")
            return
        
        print(f"🔍 找到 {len(stuck_articles)} 篇状态为'processing'的文章:")
        for article in stuck_articles:
            print(f"  - ID: {article.text_id}, 标题: {article.text_title}, 状态: {article.processing_status}")
        
        # 自动删除（不需要确认）
        print(f"\n🗑️  开始删除这 {len(stuck_articles)} 篇文章...")
        
        # 删除文章（级联删除相关句子、tokens等）
        deleted_count = 0
        for article in stuck_articles:
            try:
                print(f"🗑️  正在删除文章: {article.text_title} (ID: {article.text_id})")
                session.delete(article)
                deleted_count += 1
            except Exception as e:
                print(f"❌ 删除文章 {article.text_id} 失败: {e}")
        
        # 提交删除
        session.commit()
        print(f"\n✅ 成功删除 {deleted_count} 篇文章")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 删除失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    delete_stuck_articles()

