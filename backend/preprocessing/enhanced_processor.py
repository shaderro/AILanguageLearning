#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版文章处理模块
集成句子分割、token分割、难度评估和词汇解释功能
"""

import json
import os
from typing import Dict, Any, List, Optional
from .sentence_processor import split_sentences
from .token_processor import split_tokens, create_token_with_id

class EnhancedArticleProcessor:
    """增强版文章处理器"""
    
    def __init__(self, output_base_dir: str = "data"):
        """
        初始化增强版文章处理器
        
        Args:
            output_base_dir: 输出基础目录
        """
        self.output_base_dir = output_base_dir
        os.makedirs(output_base_dir, exist_ok=True)
        
        # 初始化难度评估器（可选）
        self.difficulty_estimator = None
        # 初始化lemma处理器（可选）
        self.lemma_processor = None
        # 词汇转换/存储（可选，若主项目提供）
        self.vocab_converter = None
        self.vocab_counter = 1
        
        # 内部管理：按lemma聚合的词汇库
        self.vocab_expressions: List[Dict[str, Any]] = []
        self.lemma_to_vocab_id: Dict[str, int] = {}
        
        # 是否启用高级功能
        self.enable_difficulty_estimation = False
        self.enable_vocab_explanation = False
    
    def enable_advanced_features(self, enable_difficulty: bool = True, enable_vocab: bool = True):
        """
        启用高级功能
        
        Args:
            enable_difficulty: 是否启用难度评估
            enable_vocab: 是否启用词汇解释
        """
        self.enable_difficulty_estimation = enable_difficulty
        self.enable_vocab_explanation = enable_vocab
        
        if enable_difficulty:
            self._init_difficulty_estimator()
            self._init_lemma_processor()  # lemma功能通常与难度评估一起使用
        
        if enable_vocab:
            self._init_vocab_converter()
    
    def _init_difficulty_estimator(self):
        """初始化难度评估器"""
        try:
            from preprocessing.single_token_difficulty_estimation import SingleTokenDifficultyEstimator
            self.difficulty_estimator = SingleTokenDifficultyEstimator()
            print("✅ 难度评估器初始化成功")
        except ImportError as e:
            print(f"❌ 无法导入难度评估器: {e}")
            self.enable_difficulty_estimation = False
    
    def _init_lemma_processor(self):
        """初始化lemma处理器"""
        try:
            from preprocessing.get_lemma import get_lemma
            self.lemma_processor = get_lemma
            print("✅ Lemma处理器初始化成功")
        except ImportError as e:
            print(f"❌ 无法导入lemma处理器: {e}")
            self.lemma_processor = None
    
    def _init_vocab_converter(self):
        """初始化词汇转换器"""
        try:
            from preprocessing.token_to_vocab import TokenToVocabConverter
            vocab_data_file = os.path.join(self.output_base_dir, "vocab_data.json")
            self.vocab_converter = TokenToVocabConverter(vocab_data_file)
            print("✅ 词汇转换器初始化成功")
        except ImportError as e:
            print(f"❌ 无法导入词汇转换器: {e}")
            self.enable_vocab_explanation = False
    
    def assess_token_difficulty(self, token_body: str, context: str = "") -> Optional[str]:
        """
        评估token的难度级别
        
        Args:
            token_body: token内容
            context: 上下文（可选）
            
        Returns:
            str: 难度级别 ("easy" 或 "hard")，如果评估失败返回None
        """
        if not self.enable_difficulty_estimation or not self.difficulty_estimator:
            return None
        
        try:
            # 只对text类型的token进行难度评估
            if not token_body or not token_body.strip():
                return None
            
            # 调用难度评估器
            difficulty_result = self.difficulty_estimator.run(token_body, verbose=False)
            
            # 处理返回结果
            if isinstance(difficulty_result, dict) and 'difficulty' in difficulty_result:
                difficulty = difficulty_result['difficulty'].lower()
                if difficulty in ['easy', 'hard']:
                    return difficulty
            elif isinstance(difficulty_result, str):
                # 尝试解析JSON字符串
                try:
                    import json
                    parsed = json.loads(difficulty_result)
                    if isinstance(parsed, dict) and 'difficulty' in parsed:
                        difficulty = parsed['difficulty'].lower()
                        if difficulty in ['easy', 'hard']:
                            return difficulty
                except json.JSONDecodeError:
                    pass
                # 尝试直接匹配
                difficulty_result_clean = difficulty_result.strip().lower()
                if difficulty_result_clean in ['easy', 'hard']:
                    return difficulty_result_clean
            
            print(f"⚠️  警告：token '{token_body}' 的难度评估结果格式异常: '{difficulty_result}'")
            return "easy"  # 默认返回easy
                
        except Exception as e:
            print(f"❌ 评估token '{token_body}' 难度时发生错误: {e}")
            return None
    
    def get_token_lemma(self, token_body: str) -> Optional[str]:
        """
        获取token的lemma形式
        
        Args:
            token_body: token内容
            
        Returns:
            str: lemma形式，如果无法获取则返回None
        """
        if not self.lemma_processor:
            return None
            
        try:
            # 只对text类型的token进行lemma处理
            if not token_body or not token_body.strip():
                return None
            
            # 调用lemma处理器
            lemma = self.lemma_processor(token_body)
            return lemma
            
        except Exception as e:
            print(f"❌ 获取token '{token_body}' 的lemma时发生错误: {e}")
            return None
    
    def _get_vocab_key(self, token_body: str, lemma: Optional[str]) -> str:
        """得到用于归并的词汇key（lemma优先，均小写）"""
        base = lemma if lemma and lemma.strip() else token_body
        return (base or "").lower()
    
    def _call_vocab_explanation(self, sentence_body: str, vocab_body: str) -> Optional[str]:
        """调用词汇解释Agent，失败则返回None"""
        try:
            from assistants.sub_assistants.vocab_explanation import VocabExplanationAssistant  # type: ignore
            class _S:  # 轻量对象，满足 .sentence_body 访问
                def __init__(self, body):
                    self.sentence_body = body
            assistant = VocabExplanationAssistant()
            result = assistant.run(_S(sentence_body), vocab_body)
            # 解析返回结构（可能已经是JSON或字符串）
            if isinstance(result, dict) and "explanation" in result:
                return result["explanation"]
            if isinstance(result, str):
                return result
            return None
        except Exception:
            return None
    
    def _call_vocab_example_explanation(self, sentence_body: str, vocab_body: str) -> Optional[str]:
        """调用上下文例句解释Agent，失败则返回句子本身"""
        try:
            from assistants.sub_assistants.vocab_example_explanation import VocabExampleExplanationAssistant  # type: ignore
            class _S:
                def __init__(self, body):
                    self.sentence_body = body
            assistant = VocabExampleExplanationAssistant()
            result = assistant.run(vocab_body, _S(sentence_body))
            if isinstance(result, dict) and "explanation" in result:
                return result["explanation"]
            if isinstance(result, str):
                return result
        except Exception:
            pass
        return sentence_body  # 兜底为原句
    
    def _add_example_to_vocab(self, vocab_id: int, text_id: int, sentence_id: int, context_explanation: str, token_indices: List[int]):
        """向已有vocab添加例句"""
        for vocab in self.vocab_expressions:
            if vocab.get("vocab_id") == vocab_id:
                examples = vocab.setdefault("examples", [])
                examples.append({
                    "vocab_id": vocab_id,
                    "text_id": text_id,
                    "sentence_id": sentence_id,
                    "context_explanation": context_explanation,
                    "token_indices": token_indices,
                })
                return
    
    def _ensure_vocab_and_example(self, key: str, text_id: int, sentence_id: int, sentence_body: str, token_sentence_index: int) -> int:
        """
        确保存在以key(lemma)为主体的vocab；不存在则创建，同时加入当前句子的example；返回vocab_id
        """
        # 已存在 -> 添加例子
        if key in self.lemma_to_vocab_id:
            vocab_id = self.lemma_to_vocab_id[key]
            ctx = self._call_vocab_example_explanation(sentence_body, key) if self.enable_vocab_explanation else sentence_body
            self._add_example_to_vocab(vocab_id, text_id, sentence_id, ctx, [token_sentence_index])
            return vocab_id
        
        # 不存在 -> 新建
        vocab_id = self.vocab_counter
        self.vocab_counter += 1
        explanation = self._call_vocab_explanation(sentence_body, key) if self.enable_vocab_explanation else None
        vocab_entry = {
            "vocab_id": vocab_id,
            "vocab_body": key,
            "explanation": explanation or "",
            "source": "auto",
            "is_starred": False,
            "examples": []
        }
        self.vocab_expressions.append(vocab_entry)
        self.lemma_to_vocab_id[key] = vocab_id
        # 添加首个例子
        ctx = self._call_vocab_example_explanation(sentence_body, key) if self.enable_vocab_explanation else sentence_body
        self._add_example_to_vocab(vocab_id, text_id, sentence_id, ctx, [token_sentence_index])
        return vocab_id
    
    def generate_vocab_for_token(self, token: Dict[str, Any], sentence_body: str, text_id: int, sentence_id: int) -> Optional[Dict[str, Any]]:
        """
        为token生成词汇解释（保持兼容的方法，内部转到lemma聚合逻辑）
        """
        if not (self.enable_vocab_explanation or self.enable_difficulty_estimation):
            return None
        if not (token["token_type"] == "text" and token.get("difficulty_level") == "hard"):
            return None
        key = self._get_vocab_key(token.get("token_body", ""), token.get("lemma"))
        if not key:
            return None
        vocab_id = self._ensure_vocab_and_example(key, text_id, sentence_id, sentence_body, token.get("sentence_token_id", 0))
        # 返回该vocab的对象引用
        for vocab in self.vocab_expressions:
            if vocab.get("vocab_id") == vocab_id:
                return vocab
        return None
    
    def process_article_enhanced(self, raw_text: str, text_id: int = 1, text_title: str = "Article") -> Dict[str, Any]:
        """
        增强版文章处理，包含难度评估和词汇解释
        
        Args:
            raw_text: 原始文章文本
            text_id: 文章ID
            text_title: 文章标题
            
        Returns:
            Dict[str, Any]: 结构化的文章数据
        """
        print(f"开始处理文章: {text_title}")
        print(f"文章ID: {text_id}")
        print(f"原始文本长度: {len(raw_text)} 字符")
        print(f"难度评估: {'启用' if self.enable_difficulty_estimation else '禁用'}")
        print(f"词汇解释: {'启用' if self.enable_vocab_explanation else '禁用'}")
        
        # 清空词库（单次处理隔离）
        self.vocab_expressions = []
        self.lemma_to_vocab_id = {}
        
        # 步骤1: 分割句子
        print("\n步骤1: 分割句子...")
        sentences_text = split_sentences(raw_text)
        print(f"分割得到 {len(sentences_text)} 个句子")
        
        # 步骤2: 为每个句子分割tokens并创建结构化数据
        print("\n步骤2: 分割tokens并创建结构化数据...")
        sentences = []
        global_token_id = 0
        
        for sentence_id, sentence_text in enumerate(sentences_text, 1):
            print(f"  处理句子 {sentence_id}/{len(sentences_text)}: {sentence_text[:50]}...")
            
            # 分割tokens
            token_dicts = split_tokens(sentence_text)
            
            # 为每个token添加ID和高级信息
            tokens_with_id = []
            for token_id, token_dict in enumerate(token_dicts, 1):
                # 基础token信息
                token_with_id = create_token_with_id(token_dict, global_token_id, token_id)
                
                # 添加高级信息
                if self.enable_difficulty_estimation and token_dict["token_type"] == "text":
                    # 评估难度
                    difficulty_level = self.assess_token_difficulty(token_dict["token_body"], sentence_text)
                    token_with_id["difficulty_level"] = difficulty_level
                    
                    # 获取lemma
                    lemma = self.get_token_lemma(token_dict["token_body"])
                    token_with_id["lemma"] = lemma
                    
                    # 生成/追加词汇解释（如果是hard难度）
                    if self.enable_vocab_explanation and difficulty_level == "hard":
                        vocab = self.generate_vocab_for_token(
                            token_with_id, sentence_text, text_id, sentence_id
                        )
                        if vocab:
                            token_with_id["linked_vocab_id"] = vocab.get("vocab_id")
                
                # 添加其他字段
                token_with_id["pos_tag"] = token_with_id.get("pos_tag")
                token_with_id["is_grammar_marker"] = token_with_id.get("is_grammar_marker", False)
                
                tokens_with_id.append(token_with_id)
                global_token_id += 1
            
            # 创建句子数据
            sentence_data = {
                "sentence_id": sentence_id,
                "sentence_body": sentence_text,
                "tokens": tokens_with_id,
                "token_count": len(tokens_with_id)
            }
            
            sentences.append(sentence_data)
        
        # 步骤3: 创建最终结果
        print("\n步骤3: 创建结构化数据对象...")
        result = {
            "text_id": text_id,
            "text_title": text_title,
            "sentences": sentences,
            "total_sentences": len(sentences),
            "total_tokens": global_token_id,
            "vocab_expressions": self.vocab_expressions
        }
        
        print(f"✅ 文章处理完成！")
        print(f"   总句子数: {len(sentences)}")
        print(f"   总token数: {global_token_id}")
        print(f"   生成词汇解释: {len(self.vocab_expressions)} 个")
        
        return result
    
    def save_enhanced_data(self, result: Dict[str, Any], output_dir: str = "data"):
        """
        保存增强版结构化数据到JSON文件
        
        Args:
            result: 结构化的文章数据
            output_dir: 输出目录
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建子目录
        text_dir = os.path.join(output_dir, f"text_{result['text_id']:03d}")
        os.makedirs(text_dir, exist_ok=True)
        
        # 保存original_text.json
        original_text_data = {
            "text_id": result["text_id"],
            "text_title": result["text_title"],
            "text_by_sentence": [
                {
                    "text_id": result["text_id"],
                    "sentence_id": sentence["sentence_id"],
                    "sentence_body": sentence["sentence_body"],
                    "grammar_annotations": [],
                    "vocab_annotations": [],
                    "tokens": sentence["tokens"]
                }
                for sentence in result["sentences"]
            ]
        }
        
        with open(os.path.join(text_dir, "original_text.json"), 'w', encoding='utf-8') as f:
            json.dump(original_text_data, f, ensure_ascii=False, indent=2)
        
        # 保存sentences.json
        sentences_data = [
            {
                "text_id": result["text_id"],
                "sentence_id": sentence["sentence_id"],
                "sentence_body": sentence["sentence_body"],
                "grammar_annotations": [],
                "vocab_annotations": [],
                "tokens": sentence["tokens"]
            }
            for sentence in result["sentences"]
        ]
        
        with open(os.path.join(text_dir, "sentences.json"), 'w', encoding='utf-8') as f:
            json.dump(sentences_data, f, ensure_ascii=False, indent=2)
        
        # 保存tokens.json (所有tokens的扁平化列表)
        all_tokens = []
        for sentence in result["sentences"]:
            for token in sentence["tokens"]:
                all_tokens.append({
                    "token_body": token["token_body"],
                    "token_type": token["token_type"],
                    "difficulty_level": token.get("difficulty_level"),
                    "global_token_id": token["global_token_id"],
                    "sentence_token_id": token["sentence_token_id"],
                    "sentence_id": sentence["sentence_id"],
                    "text_id": result["text_id"],
                    "linked_vocab_id": token.get("linked_vocab_id"),
                    "pos_tag": token.get("pos_tag"),
                    "lemma": token.get("lemma"),
                    "is_grammar_marker": token.get("is_grammar_marker", False)
                })
        
        with open(os.path.join(text_dir, "tokens.json"), 'w', encoding='utf-8') as f:
            json.dump(all_tokens, f, ensure_ascii=False, indent=2)
        
        # 保存vocab_data.json（如果有词汇解释）
        if result.get("vocab_expressions"):
            vocab_data = {
                "vocab_expressions": result["vocab_expressions"]
            }
            with open(os.path.join(text_dir, "vocab_data.json"), 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据已保存到目录: {text_dir}")
        print(f"   生成文件:")
        print(f"   - original_text.json")
        print(f"   - sentences.json") 
        print(f"   - tokens.json")
        if result.get("vocab_expressions"):
            print(f"   - vocab_data.json") 