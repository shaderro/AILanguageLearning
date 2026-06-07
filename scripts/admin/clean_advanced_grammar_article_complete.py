#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全清理 "Advanced English Grammar Structures" 文章的所有知识点数据和聊天记录
恢复干净的测试环境
"""

import sqlite3
import os
import sys
import json
from typing import List, Dict, Any

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
# 获取项目根目录
script_dir = str(REPO_ROOT)
db_path = os.path.join(str(REPO_ROOT), "database_system", "data_storage", "data", "dev.db")

# 文章信息
TARGET_USER_ID = 2
TARGET_ARTICLE_TITLE = "Advanced English Grammar Structures"
TARGET_TEXT_ID = 1771150777  # 从日志中获取的 text_id

def clean_article_data_complete(db_path: str, user_id: int, text_id: int, article_title: str):
    """完全清理指定文章的所有数据"""
    
    print("=" * 80)
    print(f"完全清理文章数据: {article_title}")
    print(f"用户ID: {user_id}, 文章ID: {text_id}")
    print("=" * 80)
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 验证文章存在
        cursor.execute("SELECT text_id, text_title, language FROM original_texts WHERE text_id = ? AND user_id = ?", 
                       (text_id, user_id))
        article = cursor.fetchone()
        
        if not article:
            print(f"⚠️  文章不存在: text_id={text_id}, user_id={user_id}")
            return False
        
        print(f"✅ 找到文章: {article[1]} (text_id={article[0]}, language={article[2]})")
        
        total_deleted = 0
        
        # ========== 1. 清理 Grammar Notations ==========
        print(f"\n📋 [1/7] 清理 Grammar Notations...")
        cursor.execute("SELECT COUNT(*) FROM grammar_notations WHERE user_id = ? AND text_id = ?", 
                       (user_id, text_id))
        grammar_notation_count = cursor.fetchone()[0]
        print(f"   找到 {grammar_notation_count} 个 grammar notations")
        
        if grammar_notation_count > 0:
            cursor.execute("DELETE FROM grammar_notations WHERE user_id = ? AND text_id = ?", 
                          (user_id, text_id))
            print(f"   ✅ 已删除 {grammar_notation_count} 个 grammar notations")
            total_deleted += grammar_notation_count
        
        # ========== 2. 清理 Grammar Examples ==========
        print(f"\n📋 [2/7] 清理 Grammar Examples...")
        cursor.execute("SELECT COUNT(*) FROM grammar_examples WHERE text_id = ?", (text_id,))
        grammar_example_count = cursor.fetchone()[0]
        print(f"   找到 {grammar_example_count} 个 grammar examples")
        
        # 获取相关的 rule_id（在删除前）
        cursor.execute("SELECT DISTINCT rule_id FROM grammar_examples WHERE text_id = ?", (text_id,))
        related_rule_ids = [row[0] for row in cursor.fetchall()]
        print(f"   相关的 grammar rule IDs: {related_rule_ids}")
        
        if grammar_example_count > 0:
            cursor.execute("DELETE FROM grammar_examples WHERE text_id = ?", (text_id,))
            print(f"   ✅ 已删除 {grammar_example_count} 个 grammar examples")
            total_deleted += grammar_example_count
        
        # ========== 3. 清理 Grammar Rules（如果没有其他 examples）==========
        print(f"\n📋 [3/7] 清理 Grammar Rules...")
        deleted_rule_count = 0
        for rule_id in related_rule_ids:
            if rule_id is None:
                continue
            # 检查该 rule 是否还有其他 examples
            cursor.execute("SELECT COUNT(*) FROM grammar_examples WHERE rule_id = ?", (rule_id,))
            remaining_examples = cursor.fetchone()[0]
            
            # 检查该 rule 是否还有其他 notations
            cursor.execute("SELECT COUNT(*) FROM grammar_notations WHERE grammar_id = ?", (rule_id,))
            remaining_notations = cursor.fetchone()[0]
            
            if remaining_examples == 0 and remaining_notations == 0:
                # 检查该 rule 是否属于当前用户
                cursor.execute("SELECT user_id FROM grammar_rules WHERE rule_id = ?", (rule_id,))
                rule_user = cursor.fetchone()
                if rule_user and rule_user[0] == user_id:
                    cursor.execute("DELETE FROM grammar_rules WHERE rule_id = ?", (rule_id,))
                    deleted_rule_count += 1
                    print(f"   ✅ 已删除 grammar rule: rule_id={rule_id}")
                else:
                    print(f"   ⏭️  跳过 grammar rule: rule_id={rule_id} (不属于当前用户)")
            else:
                print(f"   ⏭️  保留 grammar rule: rule_id={rule_id} (还有 {remaining_examples} 个 examples, {remaining_notations} 个 notations)")
        
        if deleted_rule_count > 0:
            print(f"   ✅ 总共删除了 {deleted_rule_count} 个 grammar rules")
            total_deleted += deleted_rule_count
        
        # ========== 4. 清理 Vocab Notations ==========
        print(f"\n📋 [4/7] 清理 Vocab Notations...")
        cursor.execute("SELECT COUNT(*) FROM vocab_notations WHERE user_id = ? AND text_id = ?", 
                       (user_id, text_id))
        vocab_notation_count = cursor.fetchone()[0]
        print(f"   找到 {vocab_notation_count} 个 vocab notations")
        
        if vocab_notation_count > 0:
            cursor.execute("DELETE FROM vocab_notations WHERE user_id = ? AND text_id = ?", 
                          (user_id, text_id))
            print(f"   ✅ 已删除 {vocab_notation_count} 个 vocab notations")
            total_deleted += vocab_notation_count
        
        # ========== 5. 清理 Vocab Examples ==========
        print(f"\n📋 [5/7] 清理 Vocab Examples...")
        cursor.execute("SELECT COUNT(*) FROM vocab_expression_examples WHERE text_id = ?", (text_id,))
        vocab_example_count = cursor.fetchone()[0]
        print(f"   找到 {vocab_example_count} 个 vocab examples")
        
        # 获取相关的 vocab_id（在删除前）
        cursor.execute("SELECT DISTINCT vocab_id FROM vocab_expression_examples WHERE text_id = ?", (text_id,))
        related_vocab_ids = [row[0] for row in cursor.fetchall()]
        print(f"   相关的 vocab IDs: {related_vocab_ids}")
        
        if vocab_example_count > 0:
            cursor.execute("DELETE FROM vocab_expression_examples WHERE text_id = ?", (text_id,))
            print(f"   ✅ 已删除 {vocab_example_count} 个 vocab examples")
            total_deleted += vocab_example_count
        
        # ========== 6. 清理 Vocab Expressions（如果没有其他 examples）==========
        print(f"\n📋 [6/7] 清理 Vocab Expressions...")
        deleted_vocab_count = 0
        for vocab_id in related_vocab_ids:
            if vocab_id is None:
                continue
            # 检查该 vocab 是否还有其他 examples
            cursor.execute("SELECT COUNT(*) FROM vocab_expression_examples WHERE vocab_id = ?", (vocab_id,))
            remaining_examples = cursor.fetchone()[0]
            
            # 检查该 vocab 是否还有其他 notations
            cursor.execute("SELECT COUNT(*) FROM vocab_notations WHERE vocab_id = ?", (vocab_id,))
            remaining_notations = cursor.fetchone()[0]
            
            if remaining_examples == 0 and remaining_notations == 0:
                # 检查该 vocab 是否属于当前用户
                cursor.execute("SELECT user_id FROM vocab_expressions WHERE vocab_id = ?", (vocab_id,))
                vocab_user = cursor.fetchone()
                if vocab_user and vocab_user[0] == user_id:
                    cursor.execute("DELETE FROM vocab_expressions WHERE vocab_id = ?", (vocab_id,))
                    deleted_vocab_count += 1
                    print(f"   ✅ 已删除 vocab expression: vocab_id={vocab_id}")
                else:
                    print(f"   ⏭️  跳过 vocab expression: vocab_id={vocab_id} (不属于当前用户)")
            else:
                print(f"   ⏭️  保留 vocab expression: vocab_id={vocab_id} (还有 {remaining_examples} 个 examples, {remaining_notations} 个 notations)")
        
        if deleted_vocab_count > 0:
            print(f"   ✅ 总共删除了 {deleted_vocab_count} 个 vocab expressions")
            total_deleted += deleted_vocab_count
        
        # ========== 7. 清理聊天记录（JSON 文件）==========
        print(f"\n📋 [7/7] 清理聊天记录...")
        
        # 清理 dialogue_record.json
        dialogue_record_path = os.path.join(str(REPO_ROOT), "backend", "data", "current", "dialogue_record.json")
        if os.path.exists(dialogue_record_path):
            try:
                with open(dialogue_record_path, 'r', encoding='utf-8') as f:
                    dialogue_record = json.load(f)
                
                deleted_records = 0
                text_id_str = str(text_id)
                
                # dialogue_record.json 的结构是 {"texts": {"text_id": {...}}}
                texts_dict = dialogue_record.get('texts', {})
                
                # 检查是否存在该文章的记录
                if text_id_str in texts_dict:
                    article_data = texts_dict[text_id_str]
                    print(f"   🔍 找到文章记录，结构: {list(article_data.keys())}")
                    
                    if 'sentences' in article_data:
                        # 计算要删除的记录数
                        for sentence_id, records in article_data['sentences'].items():
                            deleted_records += len(records)
                            print(f"   🔍 句子 {sentence_id}: {len(records)} 条记录")
                        
                        # 删除整个文章记录
                        del texts_dict[text_id_str]
                        print(f"   ✅ 已删除文章记录: {text_id_str}")
                    elif isinstance(article_data, dict):
                        # 如果结构不同，尝试删除整个条目
                        del texts_dict[text_id_str]
                        deleted_records = 1  # 至少删除了一条
                        print(f"   ✅ 已删除文章记录（不同结构）: {text_id_str}")
                    
                    if deleted_records > 0:
                        with open(dialogue_record_path, 'w', encoding='utf-8') as f:
                            json.dump(dialogue_record, f, ensure_ascii=False, indent=2)
                        print(f"   ✅ 已删除 {deleted_records} 条聊天记录 (dialogue_record.json)")
                        total_deleted += deleted_records
                    else:
                        print(f"   ℹ️  文章记录中没有聊天记录")
                else:
                    print(f"   ℹ️  未找到该文章的聊天记录 (text_id={text_id_str})")
                    print(f"   🔍 当前存在的 text_id: {list(texts_dict.keys())[:10]}...")  # 只显示前10个
            except Exception as e:
                print(f"   ⚠️  清理聊天记录失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ℹ️  聊天记录文件不存在: {dialogue_record_path}")
        
        # 清理 dialogue_history.json（如果存在）
        dialogue_history_path = os.path.join(str(REPO_ROOT), "backend", "data", "current", "dialogue_history.json")
        if os.path.exists(dialogue_history_path):
            try:
                with open(dialogue_history_path, 'r', encoding='utf-8') as f:
                    dialogue_history = json.load(f)
                
                # dialogue_history 的结构可能是不同的，需要根据实际结构清理
                # 这里先尝试清理
                if isinstance(dialogue_history, dict) and str(text_id) in dialogue_history:
                    del dialogue_history[str(text_id)]
                    with open(dialogue_history_path, 'w', encoding='utf-8') as f:
                        json.dump(dialogue_history, f, ensure_ascii=False, indent=2)
                    print(f"   ✅ 已清理 dialogue_history.json")
            except Exception as e:
                print(f"   ⚠️  清理 dialogue_history.json 失败: {e}")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ 清理完成！共清理 {total_deleted} 条记录")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("=" * 80)
    print("完全清理 Advanced English Grammar Structures 文章数据")
    print("=" * 80)
    
    success = clean_article_data_complete(
        db_path=db_path,
        user_id=TARGET_USER_ID,
        text_id=TARGET_TEXT_ID,
        article_title=TARGET_ARTICLE_TITLE
    )
    
    if success:
        print("\n✅ 所有数据已清理完成，测试环境已恢复干净状态")
    else:
        print("\n❌ 清理失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()

