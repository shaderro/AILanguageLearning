#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语法分析助手
继承自SubAssistant，用于分析句子的语法结构
"""

from .sub_assistant import SubAssistant
from ..utils.promp import grammar_analysis_sys_prompt, grammar_analysis_prompt_template

class GrammarAnalysisAssistant(SubAssistant):
    """语法分析助手"""
    
    def __init__(self):
        """
        初始化语法分析助手
        
        配置：
        - sys_prompt: 语法分析系统提示
        - max_tokens: 最大输出token数
        - parse_json: 是否解析JSON输出
        """
        super().__init__(
            sys_prompt=grammar_analysis_sys_prompt,
            max_tokens=500,  # 语法分析可能需要更多token
            parse_json=True   # 需要解析JSON输出
        )
    
    def build_prompt(self, sentence: str, context: str = "") -> str:
        """
        构建语法分析的prompt
        
        Args:
            sentence: 需要分析的句子
            context: 句子的上下文（可选）
            
        Returns:
            str: 格式化的prompt
        """
        return grammar_analysis_prompt_template.format(
            sentence=sentence,
            context=context if context else ""
        )
    
    def analyze_grammar(self, sentence: str, context: str = "") -> dict:
        """
        分析句子的语法结构
        
        Args:
            sentence: 需要分析的句子
            context: 句子的上下文（可选）
            
        Returns:
            dict: 包含语法分析结果的字典
            {
                "explanation": "语法讲解，详细到成分和从句类型",
                "keywords": ["关键词1", "关键词2", ...]
            }
        """
        try:
            result = self.run(sentence, context)
            
            # 验证返回结果的格式
            if isinstance(result, dict):
                if "explanation" in result and "keywords" in result:
                    return result
                else:
                    print(f"⚠️  警告：返回结果缺少必要字段: {result}")
                    return {
                        "explanation": "语法分析失败：返回结果格式不正确",
                        "keywords": []
                    }
            else:
                print(f"⚠️  警告：返回结果不是字典格式: {type(result)}")
                return {
                    "explanation": "语法分析失败：返回结果格式不正确",
                    "keywords": []
                }
                
        except Exception as e:
            print(f"❌ 语法分析失败: {e}")
            return {
                "explanation": f"语法分析失败：{str(e)}",
                "keywords": []
            }
    
    def run(self, sentence: str, context: str = "") -> dict:
        """
        执行语法分析
        
        Args:
            sentence: 需要分析的句子
            context: 句子的上下文（可选）
            
        Returns:
            dict: 语法分析结果
        """
        return super().run(sentence, context) 