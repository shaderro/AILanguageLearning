#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import os
import sys
from typing import List, Union, Dict, Any, Optional
from dataclasses import dataclass, asdict
from .token_data import OriginalText, Sentence, Token, VocabExpression, VocabExpressionExample
from ..agents.single_token_difficulty_estimation import SingleTokenDifficultyEstimator
from ..utils.get_lemma import get_lemma

class TextProcessor:
    """文本处理器：将原始文本分割成结构化数据"""
    
    def __init__(self, output_base_dir: str = "data"):
        """
        初始化文本处理器
        
        Args:
            output_base_dir: 输出基础目录
        """
        self.output_base_dir = output_base_dir
        os.makedirs(output_base_dir, exist_ok=True)
        # 初始化难度评估器
        self.difficulty_estimator = SingleTokenDifficultyEstimator()
        # 初始化vocab转换器
        self.vocab_converter = None
        self.vocab_counter = 1
        
    def _init_vocab_converter(self, vocab_data_file: str = None):
        """初始化vocab转换器"""
        if self.vocab_converter is None:
            if vocab_data_file is None:
                vocab_data_file = os.path.join(self.output_base_dir, "vocab_data.json")
            from ..utils.token_to_vocab import TokenToVocabConverter
            self.vocab_converter = TokenToVocabConverter(vocab_data_file)
            self.vocab_counter = self.vocab_converter.vocab_counter
    
    def split_sentences(self, text: str) -> List[str]:
        """
        将文本按句子分隔
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 句子列表
        """
        # 使用正则表达式分割句子
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # 过滤掉空字符串并去除首尾空白
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
        
        return sentences
    
    def split_tokens(self, text: str) -> List[Dict[str, Any]]:
        """
        将文本分割成tokens
        
        Args:
            text: 输入文本
            
        Returns:
            List[Dict[str, Any]]: token列表
        """
        if not text:
            return []
        
        tokens = []
        
        # 使用正则表达式匹配不同类型的token
        word_pattern = r'\b[\w\'-]+\b'
        punctuation_pattern = r'[^\w\s]'
        space_pattern = r'\s+'
        
        # 组合所有模式
        combined_pattern = f'({word_pattern})|({punctuation_pattern})|({space_pattern})'
        
        matches = re.finditer(combined_pattern, text)
        
        for match in matches:
            token_body = match.group(0)
            
            # 确定token类型
            if match.group(1):  # 单词
                token_type = "text"
            elif match.group(2):  # 标点符号
                token_type = "punctuation"
            elif match.group(3):  # 空白字符
                token_type = "space"
            else:
                continue
            
            token = {
                "token_body": token_body,
                "token_type": token_type
            }
            
            tokens.append(token)
        
        return tokens
    
    def assess_token_difficulty(self, token_body: str, context: str = "") -> str:
        """
        评估token的难度级别
        
        Args:
            token_body: token内容
            context: 上下文（可选）
            
        Returns:
            str: 难度级别 ("easy" 或 "hard")
        """
        try:
            # 只对text类型的token进行难度评估
            if not token_body or not token_body.strip():
                return None
            
            # 调用难度评估器
            difficulty_result = self.difficulty_estimator.run(token_body, verbose=False)
            
            # 清理结果，确保只返回 "easy" 或 "hard"
            difficulty_result = difficulty_result.strip().lower()
            if difficulty_result in ["easy", "hard"]:
                return difficulty_result
            else:
                # 如果结果不是预期的格式，返回默认值
                print(f"⚠️  警告：token '{token_body}' 的难度评估结果格式异常: '{difficulty_result}'")
                return "easy"  # 默认返回easy
                
        except Exception as e:
            print(f"❌ 评估token '{token_body}' 难度时发生错误: {e}")
            return None
    
    def get_token_lemma(self, token_body: str) -> str:
        """
        获取token的lemma形式
        
        Args:
            token_body: token内容
            
        Returns:
            str: lemma形式，如果无法获取则返回None
        """
        try:
            # 只对text类型的token进行lemma处理
            if not token_body or not token_body.strip():
                return None
            
            # 调用get_lemma函数
            lemma = get_lemma(token_body)
            return lemma
            
        except Exception as e:
            print(f"❌ 获取token '{token_body}' 的lemma时发生错误: {e}")
            return None
    
    def process_text_to_structured_data(self, text: Union[str, str], text_id: int, text_title: str = "") -> OriginalText:
        """
        将文本处理成结构化数据
        
        Args:
            text: 文本内容或文件路径
            text_id: 文本ID
            text_title: 文本标题
            
        Returns:
            OriginalText: 结构化的文本数据
        """
        # 如果输入是文件路径，先读取文件
        if os.path.isfile(text):
            with open(text, 'r', encoding='utf-8') as file:
                text_content = file.read()
            if not text_title:
                text_title = os.path.basename(text)
        else:
            text_content = text
            if not text_title:
                text_title = f"Text_{text_id}"
        
        # 初始化vocab转换器
        self._init_vocab_converter()
        
        # 分割句子
        sentence_texts = self.split_sentences(text_content)
        
        # 创建句子对象列表
        sentences = []
        global_token_id = 0
        vocab_expressions = []  # 存储生成的vocab
        
        for sentence_id, sentence_text in enumerate(sentence_texts, 1):
            # 分割tokens
            token_dicts = self.split_tokens(sentence_text)
            
            # 创建Token对象列表
            tokens = []
            for token_id, token_dict in enumerate(token_dicts, 1):
                # 评估难度级别和获取lemma（只对text类型的token）
                difficulty_level = None
                lemma = None
                if token_dict["token_type"] == "text":
                    difficulty_level = self.assess_token_difficulty(token_dict["token_body"], sentence_text)
                    lemma = self.get_token_lemma(token_dict["token_body"])
                
                token = Token(
                    token_body=token_dict["token_body"],
                    token_type=token_dict["token_type"],
                    global_token_id=global_token_id,
                    sentence_token_id=token_id,
                    difficulty_level=difficulty_level,
                    lemma=lemma,
                    linked_vocab_id=None  # 初始化为None，稍后更新
                )
                tokens.append(token)
                global_token_id += 1
            
            # 创建Sentence对象
            sentence = Sentence(
                text_id=text_id,
                sentence_id=sentence_id,
                sentence_body=sentence_text,
                grammar_annotations=[],
                vocab_annotations=[],
                tokens=tokens
            )
            sentences.append(sentence)
            
            # 为hard难度的token生成vocab
            for token in tokens:
                if token.token_type == "text" and token.difficulty_level == "hard":
                    vocab = self._generate_vocab_for_token(token, sentence, text_id)
                    if vocab:
                        vocab_expressions.append(vocab)
                        # 更新token的linked_vocab_id
                        token.linked_vocab_id = vocab.vocab_id
        
        # 创建OriginalText对象
        original_text = OriginalText(
            text_id=text_id,
            text_title=text_title,
            text_by_sentence=sentences
        )
        
        # 保存vocab数据
        if vocab_expressions:
            self._save_vocab_data(vocab_expressions)
        
        return original_text
    
    def save_structured_data(self, original_text: OriginalText, output_dir: str):
        """
        保存结构化数据到指定目录（优化版本，避免重复冗余）
        
        Args:
            original_text: 结构化的文本数据
            output_dir: 输出目录路径
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 保存 original_texts.json（只保留整体文本和 metadata）
        original_text_data = {
            "text_id": original_text.text_id,
            "text_title": original_text.text_title,
            "text_body": "\n".join([sentence.sentence_body for sentence in original_text.text_by_sentence]),
            "sentence_ids": [sentence.sentence_id for sentence in original_text.text_by_sentence]
        }
        
        with open(os.path.join(output_dir, "original_texts.json"), 'w', encoding='utf-8') as f:
            json.dump(original_text_data, f, ensure_ascii=False, indent=2)
        
        # 2. 保存 sentences.json（按 sentence 拆分，避免重复 text_id）
        sentences_data = []
        for sentence in original_text.text_by_sentence:
            # 收集该句子的所有token IDs
            token_ids = [token.global_token_id for token in sentence.tokens]
            
            sentence_data = {
                "sentence_id": sentence.sentence_id,
                "text_id": sentence.text_id,
                "sentence_body": sentence.sentence_body,
                "token_ids": token_ids,
                "grammar_annotations": sentence.grammar_annotations,
                "vocab_annotations": sentence.vocab_annotations
            }
            sentences_data.append(sentence_data)
        
        with open(os.path.join(output_dir, "sentences.json"), 'w', encoding='utf-8') as f:
            json.dump(sentences_data, f, ensure_ascii=False, indent=2)
        
        # 3. 保存 tokens.json（独立保存所有 token 信息，提供全局索引）
        all_tokens = []
        for sentence in original_text.text_by_sentence:
            for token_index, token in enumerate(sentence.tokens):
                token_data = {
                    "text_id": sentence.text_id,
                    "token_id": token.global_token_id,
                    "sentence_id": sentence.sentence_id,
                    "token_body": token.token_body,
                    "token_type": token.token_type,
                    "sentence_token_index": token_index,
                    "difficulty_level": token.difficulty_level,
                    "linked_vocab_id": token.linked_vocab_id,
                    "pos_tag": token.pos_tag,
                    "lemma": token.lemma,
                    "is_grammar_marker": token.is_grammar_marker
                }
                all_tokens.append(token_data)
        
        with open(os.path.join(output_dir, "tokens.json"), 'w', encoding='utf-8') as f:
            json.dump(all_tokens, f, ensure_ascii=False, indent=2)
    
    def process_file(self, input_path: str, text_id: int, output_dir: str = None) -> bool:
        """
        处理文本文件并保存结构化数据
        
        Args:
            input_path: 输入文件路径
            text_id: 文本ID
            output_dir: 输出目录路径，如果为None则使用默认路径
            
        Returns:
            bool: 处理是否成功
        """
        try:
            if output_dir is None:
                output_dir = os.path.join(self.output_base_dir, f"text_{text_id:03d}")
            
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                print(f"❌ 错误：找不到文件 '{input_path}'")
                return False
            
            # 处理文本
            original_text = self.process_text_to_structured_data(input_path, text_id)
            
            # 保存数据
            self.save_structured_data(original_text, output_dir)
            
            print(f"✅ 文本处理完成！")
            print(f"📁 输出目录: {output_dir}")
            print(f"📄 句子数量: {len(original_text.text_by_sentence)}")
            print(f"🔤 总token数量: {sum(len(sentence.tokens) for sentence in original_text.text_by_sentence)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 处理文件时发生错误：{e}")
            return False
    
    def process_multiple_files(self, input_files: List[str], start_text_id: int = 1) -> int:
        """
        批量处理多个文件
        
        Args:
            input_files: 输入文件路径列表
            start_text_id: 起始文本ID
            
        Returns:
            int: 成功处理的文件数量
        """
        success_count = 0
        
        print(f"🔄 开始批量处理 {len(input_files)} 个文件...")
        print("=" * 50)
        
        for i, file_path in enumerate(input_files, start_text_id):
            print(f"\n📝 处理文件 {i-start_text_id+1}/{len(input_files)}: {file_path}")
            
            if self.process_file(file_path, i):
                success_count += 1
            else:
                print(f"⚠️  跳过文件: {file_path}")
        
        print(f"\n📊 批量处理完成！成功处理 {success_count}/{len(input_files)} 个文件")
        return success_count

    def _generate_vocab_for_token(self, token: Token, sentence: Sentence, text_id: int) -> Optional[VocabExpression]:
        """
        为单个token生成vocab
        
        Args:
            token: Token对象
            sentence: 句子对象
            text_id: 文本ID
            
        Returns:
            VocabExpression: 生成的vocab对象，如果生成失败返回None
        """
        # 检查token是否为hard难度的text类型
        if not (token.token_type == "text" and token.difficulty_level == "hard"):
            return None
        
        try:
            # 延迟导入以避免循环导入
            from ..agents import VocabExplanationAssistant, VocabExampleExplanationAssistant
            
            # 初始化助手
            vocab_explanation_assistant = VocabExplanationAssistant()
            vocab_example_assistant = VocabExampleExplanationAssistant()
            
            # 获取词汇解释
            vocab_explanation_result = vocab_explanation_assistant.run(sentence, token.token_body)
            
            # 获取上下文解释
            context_explanation_result = vocab_example_assistant.run(token.token_body, sentence)
            
            # 解析解释结果
            explanation = self._parse_explanation(vocab_explanation_result)
            context_explanation = self._parse_context_explanation(context_explanation_result)
            
            # 创建VocabExpression对象
            vocab_expression = VocabExpression(
                vocab_id=self.vocab_counter,
                vocab_body=token.lemma if token.lemma else token.token_body,  # 使用lemma
                explanation=explanation,
                source="auto",  # 标注为auto
                is_starred=False,
                examples=[]
            )
            
            # 创建VocabExpressionExample
            if context_explanation:
                vocab_example = VocabExpressionExample(
                    vocab_id=self.vocab_counter,
                    text_id=text_id,
                    sentence_id=sentence.sentence_id,
                    context_explanation=context_explanation,
                    token_indices=[token.sentence_token_id] if token.sentence_token_id else []
                )
                vocab_expression.examples.append(vocab_example)
            
            # 更新计数器
            self.vocab_counter += 1
            
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

    def _save_vocab_data(self, vocab_expressions: List[VocabExpression]):
        """
        保存vocab数据到指定路径
        
        Args:
            vocab_expressions: vocab表达式列表
        """
        try:
            # 创建vocab数据目录
            vocab_output_dir = os.path.join(self.output_base_dir, "vocab_data")
            os.makedirs(vocab_output_dir, exist_ok=True)
            
            # 读取现有数据（如果存在）
            vocab_data_file = os.path.join(vocab_output_dir, "vocab_data.json")
            existing_vocabs = []
            if os.path.exists(vocab_data_file):
                try:
                    with open(vocab_data_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        existing_vocabs = existing_data.get('vocab_expressions', [])
                except Exception as e:
                    print(f"读取现有vocab数据失败: {e}")
            
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
                existing_vocabs.append(vocab_dict)
            
            # 保存vocab数据
            vocab_data = {
                'vocab_expressions': existing_vocabs,
                'next_vocab_id': self.vocab_counter
            }
            
            with open(vocab_data_file, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 成功保存 {len(vocab_expressions)} 个vocab到 {vocab_data_file}")
            
        except Exception as e:
            print(f"❌ 保存vocab数据失败: {e}")

def main():
    """主函数：处理命令行输入的文件"""
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python text_processor.py <文件路径1> [文件路径2] [文件路径3] ...")
        print("示例: python text_processor.py input.txt")
        print("示例: python text_processor.py file1.txt file2.txt file3.txt")
        sys.exit(1)
    
    # 获取文件路径列表
    input_files = sys.argv[1:]
    
    # 创建文本处理器
    processor = TextProcessor()
    
    # 处理文件
    if len(input_files) == 1:
        # 单个文件处理
        success = processor.process_file(input_files[0], 1)
        if not success:
            sys.exit(1)
    else:
        # 批量处理
        success_count = processor.process_multiple_files(input_files)
        if success_count == 0:
            sys.exit(1)

if __name__ == "__main__":
    main() 