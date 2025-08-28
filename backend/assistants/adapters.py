"""
数据适配层（只读）
- 统一新旧数据结构的访问方式
- 提供能力探测，便于主流程渐进启用新能力
- 不修改任何上层返回协议
"""

from typing import Any, Dict, List, Optional


class DataAdapter:
    """句子级数据适配器（兼容新旧 Sentence）"""

    @staticmethod
    def has_tokens(sentence: Any) -> bool:
        """是否具备 tokens 能力（新结构）"""
        return hasattr(sentence, "tokens") and getattr(sentence, "tokens") is not None

    @staticmethod
    def get_tokens(sentence: Any) -> Optional[List[Any]]:
        """获取 tokens（若不可用返回 None）"""
        return getattr(sentence, "tokens", None) if DataAdapter.has_tokens(sentence) else None

    @staticmethod
    def get_token_count(sentence: Any) -> int:
        """获取 token 数量（无 tokens 返回 0）"""
        tokens = DataAdapter.get_tokens(sentence)
        return len(tokens) if tokens else 0

    @staticmethod
    def has_difficulty_level(sentence: Any) -> bool:
        """是否具备句子难度字段（新结构）"""
        return hasattr(sentence, "sentence_difficulty_level") and getattr(
            sentence, "sentence_difficulty_level"
        ) is not None

    @staticmethod
    def get_difficulty_level(sentence: Any) -> Optional[str]:
        """获取句子难度（若不可用返回 None）"""
        return getattr(sentence, "sentence_difficulty_level", None) if DataAdapter.has_difficulty_level(sentence) else None


class GrammarRuleAdapter:
    """语法规则适配器（兼容新结构的 Rule 与旧结构的 Bundle）"""

    @staticmethod
    def has_direct_examples(rule_or_bundle: Any) -> bool:
        """对象自身是否直接挂载 examples 列表（新结构 Rule 或旧结构 Bundle 均可为 True）"""
        return hasattr(rule_or_bundle, "examples") and isinstance(getattr(rule_or_bundle, "examples"), list)

    @staticmethod
    def get_examples(rule_or_bundle: Any) -> List[Any]:
        """获取 examples 列表（统一接口）"""
        if GrammarRuleAdapter.has_direct_examples(rule_or_bundle):
            return getattr(rule_or_bundle, "examples")
        # 旧结构也可能通过 bundle.rule.examples，但当前项目中 examples 在 bundle 上
        rule = getattr(rule_or_bundle, "rule", None)
        if rule is not None and hasattr(rule, "examples"):
            return getattr(rule, "examples")
        return []

    @staticmethod
    def get_source(rule_or_bundle: Any) -> str:
        """获取 source（新结构存在，旧结构返回默认 'qa'）"""
        # 新结构：直接在 Rule 上
        if hasattr(rule_or_bundle, "source"):
            return getattr(rule_or_bundle, "source")
        # 旧结构：尝试从 bundle.rule 上读取
        rule = getattr(rule_or_bundle, "rule", None)
        if rule is not None and hasattr(rule, "source"):
            return getattr(rule, "source")
        return "qa"

    @staticmethod
    def is_starred(rule_or_bundle: Any) -> bool:
        """是否加星（新结构存在，旧结构默认 False）"""
        if hasattr(rule_or_bundle, "is_starred"):
            return bool(getattr(rule_or_bundle, "is_starred"))
        rule = getattr(rule_or_bundle, "rule", None)
        if rule is not None and hasattr(rule, "is_starred"):
            return bool(getattr(rule, "is_starred"))
        return False


class VocabAdapter:
    """词汇表达适配器（兼容新结构的 Vocab 与旧结构的 Bundle）"""

    @staticmethod
    def has_direct_examples(vocab_or_bundle: Any) -> bool:
        """对象自身是否直接挂载 examples（新结构 Vocab）或 example（旧结构 Bundle）"""
        if hasattr(vocab_or_bundle, "examples") and isinstance(getattr(vocab_or_bundle, "examples"), list):
            return True
        if hasattr(vocab_or_bundle, "example") and isinstance(getattr(vocab_or_bundle, "example"), list):
            return True
        return False

    @staticmethod
    def get_examples(vocab_or_bundle: Any) -> List[Any]:
        """获取 examples 列表（新结构为 examples，旧结构为 example）"""
        if hasattr(vocab_or_bundle, "examples"):
            return getattr(vocab_or_bundle, "examples")
        if hasattr(vocab_or_bundle, "example"):
            return getattr(vocab_or_bundle, "example")
        # 旧结构还可能为 bundle.vocab / bundle.example
        vocab = getattr(vocab_or_bundle, "vocab", None)
        if vocab is not None and hasattr(vocab_or_bundle, "example"):
            return getattr(vocab_or_bundle, "example")
        return []

    @staticmethod
    def get_source(vocab_or_bundle: Any) -> str:
        """获取 source（新结构存在，旧结构返回默认 'qa'）"""
        if hasattr(vocab_or_bundle, "source"):
            return getattr(vocab_or_bundle, "source")
        vocab = getattr(vocab_or_bundle, "vocab", None)
        if vocab is not None and hasattr(vocab, "source"):
            return getattr(vocab, "source")
        return "qa"

    @staticmethod
    def is_starred(vocab_or_bundle: Any) -> bool:
        """是否加星（新结构存在，旧结构默认 False）"""
        if hasattr(vocab_or_bundle, "is_starred"):
            return bool(getattr(vocab_or_bundle, "is_starred"))
        vocab = getattr(vocab_or_bundle, "vocab", None)
        if vocab is not None and hasattr(vocab, "is_starred"):
            return bool(getattr(vocab, "is_starred"))
        return False

    @staticmethod
    def has_token_indices(example: Any) -> bool:
        """例子是否包含 token_indices（新结构特性）"""
        return hasattr(example, "token_indices") and getattr(example, "token_indices") is not None

    @staticmethod
    def get_token_indices(example: Any) -> List[int]:
        """获取例子的 token_indices（无则返回空列表）"""
        if VocabAdapter.has_token_indices(example):
            return list(getattr(example, "token_indices") or [])
        return []


class CapabilityDetector:
    """能力探测器：输出当前对象可用能力画像（只读）"""

    @staticmethod
    def detect_sentence_capabilities(sentence: Any) -> Dict[str, Any]:
        return {
            "has_tokens": DataAdapter.has_tokens(sentence),
            "has_difficulty_level": DataAdapter.has_difficulty_level(sentence),
            "token_count": DataAdapter.get_token_count(sentence),
        }

    @staticmethod
    def detect_grammar_rule_capabilities(rule_or_bundle: Any) -> Dict[str, Any]:
        examples = GrammarRuleAdapter.get_examples(rule_or_bundle)
        return {
            "has_examples_list": GrammarRuleAdapter.has_direct_examples(rule_or_bundle),
            "has_source": hasattr(rule_or_bundle, "source") or hasattr(getattr(rule_or_bundle, "rule", None), "source"),
            "has_is_starred": hasattr(rule_or_bundle, "is_starred") or hasattr(getattr(rule_or_bundle, "rule", None), "is_starred"),
            "examples_count": len(examples),
        }

    @staticmethod
    def detect_vocab_capabilities(vocab_or_bundle: Any) -> Dict[str, Any]:
        examples = VocabAdapter.get_examples(vocab_or_bundle)
        has_token_indices = any(VocabAdapter.has_token_indices(ex) for ex in examples)
        return {
            "has_examples_list": VocabAdapter.has_direct_examples(vocab_or_bundle),
            "has_source": hasattr(vocab_or_bundle, "source") or hasattr(getattr(vocab_or_bundle, "vocab", None), "source"),
            "has_is_starred": hasattr(vocab_or_bundle, "is_starred") or hasattr(getattr(vocab_or_bundle, "vocab", None), "is_starred"),
            "examples_count": len(examples),
            "has_token_indices": has_token_indices,
        } 