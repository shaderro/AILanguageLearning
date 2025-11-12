#!/usr/bin/env python3
"""检查数据库中的notations"""
import sys
sys.path.insert(0, '.')

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import VocabNotation, GrammarNotation

db_manager = DatabaseManager('development')
session = db_manager.get_session()

print("\n" + "="*80)
print("📊 数据库中的Vocab Notations:")
print("="*80)
vocab_notations = session.query(VocabNotation).all()
for n in vocab_notations[-5:]:  # 显示最后5条
    print(f"  ID: {n.id}, user_id: {n.user_id}, text_id: {n.text_id}, sentence_id: {n.sentence_id}, token_id: {n.token_id}, vocab_id: {n.vocab_id}")

print(f"\n总计: {len(vocab_notations)} 条")

print("\n" + "="*80)
print("📊 数据库中的Grammar Notations:")
print("="*80)
grammar_notations = session.query(GrammarNotation).all()
for n in grammar_notations[-5:]:  # 显示最后5条
    print(f"  ID: {n.id}, user_id: {n.user_id}, text_id: {n.text_id}, sentence_id: {n.sentence_id}, grammar_id: {n.grammar_id}")

print(f"\n总计: {len(grammar_notations)} 条")
print("="*80 + "\n")

session.close()

