#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token to Vocab 转换模块
将hard难度的token转换为vocab数据结构
"""

import json
import os
from typing import List, Dict, Any, Optional
from data_managers.data_classes_new import Token, VocabExpression, VocabExpressionExample

class TokenToVocabConverter:
    """Token到Vocab转换器"""
    
    def __init__(self, vocab_data_file: str = "vocab_data.json"):
        """
        初始化转换器
        
        Args:
            vocab_data_file: vocab数据存储文件路径
        """
        self.vocab_data_file = vocab_data_file
        self.vocab_counter = self._load_vocab_counter()
        
    def _load_vocab_counter(self) -> int:
        """加载vocab计数器"""
        if os.path.exists(self.vocab_data_file):
            try:
                with open(self.vocab_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('next_vocab_id', 1)
            except Exception:
                return 1
        return 1
    
    def _save_vocab_counter(self):
        """保存vocab计数器"""
        try:
            if os.path.exists(self.vocab_data_file):
                with open(self.vocab_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {'vocab_expressions': []}
            
            data['next_vocab_id'] = self.vocab_counter
            
            with open(self.vocab_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存vocab计数器失败: {e}")
    
    def convert_token_to_vocab(self, token: Token, sentence_body: str, text_id: int, sentence_id: int) -> Optional[VocabExpression]:
        """
        将token转换为vocab
        
        Args:
            token: Token对象
            sentence_body: 句子内容
            text_id: 文本ID
            sentence_id: 句子ID
            
        Returns:
            VocabExpression: 转换后的vocab对象，如果转换失败返回None
        """
        # 检查token是否为hard难度的text类型
        if not (token.token_type == "text" and token.difficulty_level == "hard"):
            return None
        
        try:
            # 延迟导入以避免循环导入
            from assistants.sub_assistants.vocab_explanation import VocabExplanationAssistant
            from assistants.sub_assistants.vocab_example_explanation import VocabExampleExplanationAssistant
            
            # 创建临时Sentence对象用于API调用
            from data_managers.data_classes_new import Sentence
            temp_sentence = Sentence(
                text_id=text_id,
                sentence_id=sentence_id,
                sentence_body=sentence_body,
                grammar_annotations=[],
                vocab_annotations=[],
                tokens=[]
            )
            
            # 初始化助手
            vocab_explanation_assistant = VocabExplanationAssistant()
            vocab_example_assistant = VocabExampleExplanationAssistant()
            
            # 获取词汇解释
            vocab_explanation_result = vocab_explanation_assistant.run(temp_sentence, token.token_body)
            
            # 获取上下文解释
            context_explanation_result = vocab_example_assistant.run(token.token_body, temp_sentence)
            
            # 解析解释结果
            explanation = self._parse_explanation(vocab_explanation_result)
            context_explanation = self._parse_context_explanation(context_explanation_result)
            
            # 创建VocabExpression对象
            vocab_expression = VocabExpression(
                vocab_id=self.vocab_counter,
                vocab_body=token.token_body,
                explanation=explanation,
                source="auto",
                is_starred=False,
                examples=[]
            )
            
            # 创建VocabExpressionExample
            if context_explanation:
                vocab_example = VocabExpressionExample(
                    vocab_id=self.vocab_counter,
                    text_id=text_id,
                    sentence_id=sentence_id,
                    context_explanation=context_explanation,
                    token_indices=[token.sentence_token_id] if token.sentence_token_id else []
                )
                vocab_expression.examples.append(vocab_example)
            
            # 更新计数器
            self.vocab_counter += 1
            self._save_vocab_counter()
            
            return vocab_expression
            
        except Exception as e:
            print(f"转换token '{token.token_body}' 到vocab失败: {e}")
            return None
    
    def _parse_explanation(self, result: Any) -> str:
        """解析词汇解释结果"""
        if isinstance(result, dict):
            return result.get('explanation', '')
        elif isinstance(result, str):
            # 尝试解析JSON字符串
            try:
                data = json.loads(result)
                return data.get('explanation', '')
            except:
                return result
        return str(result)
    
    def _parse_context_explanation(self, result: Any) -> str:
        """解析上下文解释结果"""
        if isinstance(result, dict):
            return result.get('explanation', '')
        elif isinstance(result, str):
            # 尝试解析JSON字符串
            try:
                data = json.loads(result)
                return data.get('explanation', '')
            except:
                return result
        return str(result)
    
    def convert_tokens_from_text(self, original_text) -> List[VocabExpression]:
        """
        从OriginalText对象中提取所有hard难度的token并转换为vocab
        
        Args:
            original_text: OriginalText对象
            
        Returns:
            List[VocabExpression]: 转换后的vocab列表
        """
        vocab_expressions = []
        
        for sentence in original_text.text_by_sentence:
            for token in sentence.tokens:
                vocab = self.convert_token_to_vocab(
                    token, 
                    sentence.sentence_body, 
                    original_text.text_id, 
                    sentence.sentence_id
                )
                if vocab:
                    vocab_expressions.append(vocab)
        
        return vocab_expressions
    
    def save_vocab_data(self, vocab_expressions: List[VocabExpression]):
        """
        保存vocab数据到文件
        
        Args:
            vocab_expressions: vocab表达式列表
        """
        try:
            # 读取现有数据
            if os.path.exists(self.vocab_data_file):
                with open(self.vocab_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {'vocab_expressions': []}
            
            # 添加新的vocab数据
            for vocab in vocab_expressions:
                vocab_dict = {
                    'vocab_id': vocab.vocab_id,
                    'vocab_body': vocab.vocab_body,
                    'explanation': vocab.explanation,
                    'source': vocab.source,
                    'is_starred': vocab.is_starred,
                    'examples': [
                        {
                            'vocab_id': example.vocab_id,
                            'text_id': example.text_id,
                            'sentence_id': example.sentence_id,
                            'context_explanation': example.context_explanation,
                            'token_indices': example.token_indices
                        }
                        for example in vocab.examples
                    ]
                }
                data['vocab_expressions'].append(vocab_dict)
            
            # 保存数据
            with open(self.vocab_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ 成功保存 {len(vocab_expressions)} 个vocab到 {self.vocab_data_file}")
            
        except Exception as e:
            print(f"❌ 保存vocab数据失败: {e}")

def convert_token_to_vocab(token: Token, sentence_body: str, text_id: int, sentence_id: int) -> Optional[VocabExpression]:
    """
    便捷函数：将单个token转换为vocab
    
    Args:
        token: Token对象
        sentence_body: 句子内容
        text_id: 文本ID
        sentence_id: 句子ID
        
    Returns:
        VocabExpression: 转换后的vocab对象
    """
    converter = TokenToVocabConverter()
    return converter.convert_token_to_vocab(token, sentence_body, text_id, sentence_id) 