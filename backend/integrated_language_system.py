#!/usr/bin/env python3
"""
集成语言学习系统
整合 preprocessing、assistant 和 data manager 的所有功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing.enhanced_processor import EnhancedArticleProcessor
from data_managers.data_controller import DataController
from assistants.main_assistant import MainAssistant
from data_managers.data_classes_new import Sentence as NewSentence, Token, WordToken, VocabExpression, GrammarRule, OriginalText
from typing import List, Dict, Any, Optional, Union
import json

class IntegratedLanguageSystem:
    """
    集成语言学习系统
    统一管理 preprocessing、assistant 和 data manager
    """
    
    def __init__(self, max_turns: int = 100, use_new_structure: bool = True):
        """
        初始化集成语言学习系统
        
        Args:
            max_turns: 最大对话轮数
            use_new_structure: 是否使用新数据结构
        """
        print("🔧 初始化集成语言学习系统...")
        
        # 初始化各个组件
        self._init_preprocessor()
        self._init_data_manager(max_turns, use_new_structure)
        self._init_main_assistant(max_turns)
        
        # 初始化文件结构
        self._init_file_structure()
        
        print("🎉 集成语言学习系统初始化完成！")
    
    def _init_preprocessor(self):
        """初始化预处理模块"""
        try:
            self.preprocessor = EnhancedArticleProcessor()
            self.preprocessor.enable_advanced_features(enable_difficulty=True, enable_vocab=True)
            print("✅ 预处理模块初始化完成")
        except Exception as e:
            print(f"❌ 预处理模块初始化失败: {e}")
            raise
    
    def _init_data_manager(self, max_turns: int, use_new_structure: bool):
        """初始化数据管理器"""
        try:
            self.data_controller = DataController(
                max_turns, 
                use_new_structure=use_new_structure, 
                save_to_new_data_class=use_new_structure
            )
            print("✅ 数据管理器初始化完成")
        except Exception as e:
            print(f"❌ 数据管理器初始化失败: {e}")
            raise
    
    def _init_main_assistant(self, max_turns: int):
        """初始化主助手"""
        try:
            self.main_assistant = MainAssistant(self.data_controller, max_turns)
            print("✅ 主助手初始化完成")
        except Exception as e:
            print(f"❌ 主助手初始化失败: {e}")
            raise
    
    def _init_file_structure(self):
        """初始化文件结构"""
        try:
            # 创建article文件夹
            article_dir = "data/article"
            if not os.path.exists(article_dir):
                os.makedirs(article_dir)
                print(f"✅ 创建article文件夹: {article_dir}")
            else:
                print(f"✅ article文件夹已存在: {article_dir}")
            
            # 初始化词汇和语法文件
            self.vocab_file = "data/current/vocab.json"
            self.grammar_file = "data/current/grammar.json"
            
            # 如果文件不存在，创建空文件
            if not os.path.exists(self.vocab_file):
                with open(self.vocab_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print(f"✅ 创建词汇文件: {self.vocab_file}")
            
            if not os.path.exists(self.grammar_file):
                with open(self.grammar_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print(f"✅ 创建语法文件: {self.grammar_file}")
                
        except Exception as e:
            print(f"⚠️ 文件结构初始化警告: {e}")
    
    def process_article(self, raw_text: str, text_id: int = 1, title: str = "Article") -> Dict[str, Any]:
        """
        处理文章：完整的预处理流程
        
        Args:
            raw_text: 原始文章文本
            text_id: 文章ID
            title: 文章标题
            
        Returns:
            Dict[str, Any]: 处理结果，包含句子对象和统计信息
        """
        print(f"📝 开始处理文章: {title}")
        print(f"   文章ID: {text_id}")
        print(f"   文本长度: {len(raw_text)} 字符")
        
        # 步骤1: 预处理文章
        print("\n🔧 步骤1: 预处理文章...")
        processed_data = self.preprocessor.process_article_enhanced(
            raw_text, text_id=text_id, text_title=title
        )
        
        # 步骤2: 转换为句子对象
        print("\n🔧 步骤2: 转换数据格式...")
        sentences = self._convert_to_sentences(processed_data)
        
        # 步骤3: 保存到数据管理器
        print("\n🔧 步骤3: 保存到数据管理器...")
        self._save_processed_data(processed_data, sentences)
        
        # 步骤4: 保存到文件系统
        print("\n🔧 步骤4: 保存到文件系统...")
        self._save_to_file_system(text_id, title, sentences, processed_data)
        
        # 步骤5: 返回结果
        result = {
            'sentences': sentences,
            'processed_data': processed_data,
            'statistics': {
                'total_sentences': len(sentences),
                'total_tokens': processed_data['total_tokens'],
                'vocab_count': len(processed_data.get('vocab_expressions', [])),
                'text_id': text_id,
                'title': title
            }
        }
        
        print(f"\n✅ 文章处理完成！")
        print(f"   生成句子数量: {len(sentences)}")
        print(f"   总token数量: {processed_data['total_tokens']}")
        print(f"   词汇解释数量: {len(processed_data.get('vocab_expressions', []))}")
        
        return result
    
    def _convert_to_sentences(self, processed_data: Dict[str, Any]) -> List[NewSentence]:
        """将预处理数据转换为句子对象"""
        sentences = []
        
        for sentence_data in processed_data['sentences']:
            # 计算句子难度级别
            difficulty_level = self._calculate_sentence_difficulty(sentence_data['tokens'])
            
            # 转换tokens
            tokens = self._convert_tokens_to_objects(sentence_data['tokens'])

            word_tokens = self._convert_word_tokens_to_objects(sentence_data.get('word_tokens'))
            
            # 创建NewSentence对象
            sentence = NewSentence(
                text_id=processed_data['text_id'],
                sentence_id=sentence_data['sentence_id'],
                sentence_body=sentence_data['sentence_body'],
                grammar_annotations=(),
                vocab_annotations=(),
                sentence_difficulty_level=difficulty_level,
                tokens=tokens,
                word_tokens=word_tokens
            )
            sentences.append(sentence)
        
        return sentences
    
    def _calculate_sentence_difficulty(self, tokens: List[Dict[str, Any]]) -> str:
        """根据tokens计算句子的整体难度级别"""
        if not tokens:
            return "easy"
        
        # 统计困难词汇数量
        hard_tokens = [t for t in tokens if t.get('difficulty_level') == 'hard']
        hard_ratio = len(hard_tokens) / len(tokens)
        
        if hard_ratio >= 0.3:
            return "hard"
        elif hard_ratio >= 0.1:
            return "medium"
        else:
            return "easy"
    
    def _convert_tokens_to_objects(self, tokens_data: List[Dict[str, Any]]) -> tuple:
        """将token数据转换为Token对象"""
        token_objects = []
        
        for token_data in tokens_data:
            token = Token(
                token_body=token_data.get('token_body', ''),
                token_type=token_data.get('token_type', 'text'),
                difficulty_level=token_data.get('difficulty_level'),
                global_token_id=token_data.get('global_token_id', 0),
                sentence_token_id=token_data.get('sentence_token_id', 0),
                pos_tag=token_data.get('pos_tag'),
                lemma=token_data.get('lemma'),
                is_grammar_marker=token_data.get('is_grammar_marker', False),
                linked_vocab_id=token_data.get('linked_vocab_id')
            )
            token_objects.append(token)
        
        return tuple(token_objects)

    def _convert_word_tokens_to_objects(self, word_tokens_data: Optional[List[Dict[str, Any]]]) -> Optional[tuple]:
        """将 word token 数据转换为 WordToken 对象"""
        if not word_tokens_data:
            return None

        word_token_objects = []
        for word_token in word_tokens_data:
            word_token_objects.append(
                WordToken(
                    word_token_id=word_token.get('word_token_id', 0),
                    token_ids=tuple(word_token.get('token_ids', [])),
                    word_body=word_token.get('word_body', ''),
                    pos_tag=word_token.get('pos_tag'),
                    lemma=word_token.get('lemma'),
                    linked_vocab_id=word_token.get('linked_vocab_id')
                )
            )
        return tuple(word_token_objects)
    
    def _save_processed_data(self, processed_data: Dict[str, Any], sentences: List[NewSentence]):
        """保存处理后的数据到数据管理器"""
        try:
            # 保存词汇数据
            if processed_data.get('vocab_expressions'):
                print(f"   保存 {len(processed_data['vocab_expressions'])} 个词汇解释")
                self._save_vocab_expressions(processed_data['vocab_expressions'])
            
            # 保存文章数据
            print(f"   保存文章数据: {processed_data['text_title']}")
            self._save_article_data(processed_data, sentences)
            
        except Exception as e:
            print(f"⚠️ 保存数据时出现警告: {e}")
    
    def _save_vocab_expressions(self, vocab_expressions: List[Dict[str, Any]]):
        """保存词汇表达式"""
        for vocab_data in vocab_expressions:
            try:
                # 获取下一个vocab_id
                vocab_id = self._get_next_vocab_id()
                
                # 创建VocabExpression对象
                vocab = VocabExpression(
                    vocab_id=vocab_id,
                    vocab_body=vocab_data.get('vocab_body', ''),
                    explanation=vocab_data.get('explanation', ''),
                    examples=vocab_data.get('examples', []),
                    source=vocab_data.get('source', 'preprocessing'),
                    is_starred=False
                )
                
                # 添加到数据管理器
                self.data_controller.vocab_manager.add_vocab(vocab)
                
            except Exception as e:
                print(f"⚠️ 保存词汇 '{vocab_data.get('vocab_body', 'unknown')}' 失败: {e}")
    
    def _get_next_vocab_id(self) -> int:
        """获取下一个词汇ID"""
        try:
            # 读取现有词汇文件
            if os.path.exists(self.vocab_file):
                with open(self.vocab_file, 'r', encoding='utf-8') as f:
                    vocab_list = json.load(f)
                return len(vocab_list) + 1
            else:
                return 1
        except Exception:
            return 1
    
    def _save_article_data(self, processed_data: Dict[str, Any], sentences: List[NewSentence]):
        """保存文章数据"""
        try:
            # 添加文章到文本管理器
            self.data_controller.text_manager.add_text(processed_data['text_title'])
            
            # 获取文章ID（应该是最后一个添加的文章）
            text_id = processed_data['text_id']
            
            # 添加句子到文章
            for sentence in sentences:
                self.data_controller.text_manager.add_sentence_to_text(
                    text_id, 
                    sentence.sentence_body
                )
                
        except Exception as e:
            print(f"⚠️ 保存文章数据失败: {e}")
    
    def _save_to_file_system(self, text_id: int, title: str, sentences: List[NewSentence], processed_data: Dict[str, Any]):
        """保存到文件系统"""
        try:
            # 1. 保存文章到article文件夹
            article_filename = f"article{text_id:02d}.json"
            article_path = f"data/article/{article_filename}"
            
            # 创建OriginalText对象
            original_text = OriginalText(
                text_id=text_id,
                text_title=title,
                text_by_sentence=sentences
            )
            
            # 转换为字典并保存
            article_data = {
                'text_id': original_text.text_id,
                'text_title': original_text.text_title,
                'text_by_sentence': [
                    {
                        'text_id': sentence.text_id,
                        'sentence_id': sentence.sentence_id,
                        'sentence_body': sentence.sentence_body,
                        'grammar_annotations': sentence.grammar_annotations,
                        'vocab_annotations': sentence.vocab_annotations,
                        'sentence_difficulty_level': sentence.sentence_difficulty_level,
                        'tokens': [
                            {
                                'token_body': token.token_body,
                                'token_type': token.token_type,
                                'difficulty_level': token.difficulty_level,
                                'global_token_id': token.global_token_id,
                                'sentence_token_id': token.sentence_token_id,
                                'pos_tag': token.pos_tag,
                                'lemma': token.lemma,
                                'is_grammar_marker': token.is_grammar_marker,
                                'linked_vocab_id': token.linked_vocab_id,
                                'word_token_id': token.word_token_id
                            }
                            for token in sentence.tokens
                        ],
                        'word_tokens': [
                            {
                                'word_token_id': word_token.word_token_id,
                                'word_body': word_token.word_body,
                                'token_ids': list(word_token.token_ids),
                                'pos_tag': word_token.pos_tag,
                                'lemma': word_token.lemma,
                                'linked_vocab_id': word_token.linked_vocab_id
                            }
                            for word_token in (sentence.word_tokens or [])
                        ]
                    }
                    for sentence in sentences
                ]
            }
            
            with open(article_path, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 保存文章到: {article_path}")
            
            # 2. 保存词汇到vocab.json
            if processed_data.get('vocab_expressions'):
                self._save_vocab_to_file(processed_data['vocab_expressions'])
            
        except Exception as e:
            print(f"⚠️ 保存到文件系统失败: {e}")
    
    def _save_vocab_to_file(self, vocab_expressions: List[Dict[str, Any]]):
        """保存词汇到vocab.json文件"""
        try:
            # 读取现有词汇
            vocab_list = []
            if os.path.exists(self.vocab_file):
                with open(self.vocab_file, 'r', encoding='utf-8') as f:
                    vocab_list = json.load(f)
            
            # 添加新词汇
            for vocab_data in vocab_expressions:
                vocab_id = len(vocab_list) + 1
                vocab_item = {
                    'vocab_id': vocab_id,
                    'vocab_body': vocab_data.get('vocab_body', ''),
                    'explanation': vocab_data.get('explanation', ''),
                    'examples': vocab_data.get('examples', []),
                    'source': vocab_data.get('source', 'preprocessing'),
                    'is_starred': False
                }
                vocab_list.append(vocab_item)
            
            # 保存到文件
            with open(self.vocab_file, 'w', encoding='utf-8') as f:
                json.dump(vocab_list, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 保存词汇到: {self.vocab_file}")
            
        except Exception as e:
            print(f"⚠️ 保存词汇到文件失败: {e}")
    
    def ask_question(self, sentence: NewSentence, question: str) -> str:
        """
        向指定句子提问
        
        Args:
            sentence: 句子对象
            question: 用户问题
            
        Returns:
            str: AI回答
        """
        print(f"❓ 用户问题: {question}")
        print(f"📖 引用句子: {sentence.sentence_body[:50]}...")
        
        # 使用main_assistant处理问题
        result = self.main_assistant.run(sentence, question)
        
        print(f"🤖 AI回答: {result}")
        return result
    
    def get_article_sentences(self, text_id: int) -> List[NewSentence]:
        """
        获取指定文章的句子列表
        
        Args:
            text_id: 文章ID
            
        Returns:
            List[NewSentence]: 句子列表
        """
        try:
            # 从数据管理器中获取文章
            article = self.data_controller.text_manager.get_text_by_id(text_id)
            if article and article.text_by_sentence:
                return list(article.text_by_sentence)
            return []
        except Exception as e:
            print(f"⚠️ 获取文章句子失败: {e}")
            return []
    
    def get_vocab_list(self) -> List[str]:
        """获取词汇列表"""
        return self.data_controller.vocab_manager.get_all_vocab_body()
    
    def get_grammar_rules(self) -> List[str]:
        """获取语法规则列表"""
        return self.data_controller.grammar_manager.get_all_rules_name()
    
    def get_article_list(self) -> List[Dict[str, Any]]:
        """获取文章列表"""
        try:
            articles = []
            for text_id in range(1, self.data_controller.text_manager.get_new_text_id()):
                article = self.data_controller.text_manager.get_text_by_id(text_id)
                if article:
                    articles.append({
                        'text_id': text_id,
                        'title': article.text_title,
                        'sentence_count': len(article.text_by_sentence) if article.text_by_sentence else 0
                    })
            return articles
        except Exception as e:
            print(f"⚠️ 获取文章列表失败: {e}")
            return []
    
    def save_all_data(self):
        """保存所有数据"""
        try:
            self.data_controller.save_data()
            print("✅ 所有数据保存成功")
        except Exception as e:
            print(f"❌ 数据保存失败: {e}")
    
    def load_all_data(self):
        """加载所有数据"""
        try:
            self.data_controller.load_data()
            print("✅ 所有数据加载成功")
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'vocab_count': len(self.get_vocab_list()),
            'grammar_count': len(self.get_grammar_rules()),
            'article_count': len(self.get_article_list()),
            'structure_mode': 'new' if self.data_controller.use_new_structure else 'old',
            'save_mode': 'new' if self.data_controller.save_to_new_data_class else 'old'
        }
    
    def print_system_status(self):
        """打印系统状态信息"""
        status = self.get_system_status()
        print("\n📊 系统状态:")
        print(f"   词汇数量: {status['vocab_count']}")
        print(f"   语法规则数量: {status['grammar_count']}")
        print(f"   文章数量: {status['article_count']}")
        print(f"   数据管理器: {status['structure_mode']}结构模式")
        print(f"   保存模式: {status['save_mode']}数据保存")
    
    def process_and_ask(self, raw_text: str, question: str, text_id: int = 1, title: str = "Article") -> str:
        """
        处理文章并立即提问（一站式服务）
        
        Args:
            raw_text: 原始文章文本
            question: 用户问题
            text_id: 文章ID
            title: 文章标题
            
        Returns:
            str: AI回答
        """
        # 处理文章
        result = self.process_article(raw_text, text_id, title)
        
        # 找到最相关的句子
        target_sentence = self._find_most_relevant_sentence(result['sentences'], question)
        
        if target_sentence:
            # 提问
            return self.ask_question(target_sentence, question)
        else:
            return "抱歉，没有找到相关的句子来回答您的问题。"
    
    def _find_most_relevant_sentence(self, sentences: List[NewSentence], question: str) -> Optional[NewSentence]:
        """找到最相关的句子"""
        if not sentences:
            return None
        
        # 简单的关键词匹配
        question_keywords = set(question.lower().split())
        best_sentence = None
        best_score = 0
        
        for sentence in sentences:
            sentence_words = set(sentence.sentence_body.lower().split())
            score = len(question_keywords.intersection(sentence_words))
            
            if score > best_score:
                best_score = score
                best_sentence = sentence
        
        return best_sentence

def main():
    """主函数：演示集成语言学习系统的使用"""
    print("🎯 集成语言学习系统演示")
    print("=" * 60)
    
    # 创建集成系统
    system = IntegratedLanguageSystem()
    
    # 测试文章
    test_article = """
    Learning a new language is challenging but rewarding. 
    Grammar and vocabulary are essential components of language study.
    The internet has revolutionized the way we learn languages.
    """
    
    # 一站式处理并提问
    print("\n📋 一站式处理并提问")
    print("-" * 40)
    
    question = "challenging是什么意思？"
    answer = system.process_and_ask(test_article, question, text_id=1, title="Language Learning Article")
    
    print(f"❓ 问题: {question}")
    print(f"🤖 回答: {answer}")
    
    # 打印系统状态
    system.print_system_status()
    
    print("\n🎉 演示完成！")

if __name__ == "__main__":
    main() 