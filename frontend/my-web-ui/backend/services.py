import json
import os
import sys
from typing import List, Optional, Dict, Any

from models import Vocab, GrammarRule


class DataService:
    """数据服务类，直接读取 JSON 文件提供 API 数据访问"""
    
    def __init__(self):
        # 直接使用文件读取模式，更稳定
        self._init_file_mode()
    
    def _init_file_mode(self):
        """文件读取模式：直接读取 JSON 文件"""
        print("使用文件读取模式：直接读取 JSON 文件")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 修正路径：从 frontend/my-web-ui/backend 到 backend/data/current
        self.vocab_file_path = os.path.join(current_dir, "..", "..", "..", "backend", "data", "current", "vocab.json")
        self.grammar_file_path = os.path.join(current_dir, "..", "..", "..", "backend", "data", "current", "grammar.json")
    
    def _load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """加载 JSON 文件"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"警告: 文件不存在 {file_path}")
                return []
        except Exception as e:
            print(f"错误: 读取文件失败 {file_path}: {e}")
            return []
    
    def get_vocab_data(self) -> List[Vocab]:
        """获取词汇数据"""
        raw_data = self._load_json_file(self.vocab_file_path)
        vocab_list = []
        
        for item in raw_data:
            try:
                # 转换原始数据为 Vocab 模型
                vocab = Vocab(
                    vocab_id=item.get("vocab_id", 0),
                    vocab_body=item.get("vocab_body", ""),
                    explanation=item.get("explanation", ""),
                    examples=item.get("examples", []),
                    source=item.get("source", "unknown"),
                    is_starred=item.get("is_starred", False)
                )
                vocab_list.append(vocab)
            except Exception as e:
                print(f"错误: 解析词汇数据失败: {e}")
                continue
        
        return vocab_list
    
    def get_grammar_data(self) -> List[GrammarRule]:
        """获取语法数据"""
        raw_data = self._load_json_file(self.grammar_file_path)
        grammar_list = []
        
        for item in raw_data:
            try:
                # 转换原始数据为 GrammarRule 模型
                grammar = GrammarRule(
                    rule_id=item.get("rule_id", 0),
                    rule_name=item.get("rule_name", ""),
                    rule_summary=item.get("rule_summary", ""),
                    examples=item.get("examples", []),
                    source=item.get("source", "unknown"),
                    is_starred=item.get("is_starred", False)
                )
                grammar_list.append(grammar)
            except Exception as e:
                print(f"错误: 解析语法数据失败: {e}")
                continue
        
        return grammar_list
    
    def get_vocab_by_id(self, vocab_id: int) -> Optional[Vocab]:
        """根据 ID 获取词汇"""
        vocab_list = self.get_vocab_data()
        for vocab in vocab_list:
            if vocab.vocab_id == vocab_id:
                return vocab
        return None
    
    def get_grammar_by_id(self, rule_id: int) -> Optional[GrammarRule]:
        """根据 ID 获取语法规则"""
        grammar_list = self.get_grammar_data()
        for grammar in grammar_list:
            if grammar.rule_id == rule_id:
                return grammar
        return None


# 创建全局数据服务实例
data_service = DataService()
