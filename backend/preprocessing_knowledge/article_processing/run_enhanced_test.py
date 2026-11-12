#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用增强版文章处理器对指定句子进行全流程处理的脚本。
为避免外部依赖（OpenAI等），这里注入一个本地的简易难度评估器：
- 规则：长度 > 6 的英文词判定为 hard，否则 easy。
这能触发 vocab 生成与例句聚合的完整流程。
"""

from article_processing import EnhancedArticleProcessor

def main():
    # 测试句子（用户提供）
    article = (
        "Potawatomi warriors ambushed a United States Army convoy after it had "
        "evacuated Fort Dearborn (site pictured), in present-day Chicago, and razed the fort."
    )

    # 创建增强版处理器并开启功能
    processor = EnhancedArticleProcessor(output_base_dir="enhanced_output")
    processor.enable_advanced_features(enable_difficulty=True, enable_vocab=True)

    # 注入一个简易的本地难度评估器（避免外部依赖阻塞流程）
    class LocalDummyEstimator:
        def run(self, word: str, verbose: bool = False) -> str:
            # 英文词长度 > 6 视为 hard，否则 easy
            try:
                clean = ''.join(ch for ch in word if ch.isalpha())
                return "hard" if len(clean) > 6 else "easy"
            except Exception:
                return "easy"

    # 注入一个简易的本地lemma处理器
    def local_lemma_processor(word: str) -> str:
        # 简单的lemma处理：转换为小写，去除常见后缀
        word = word.lower()
        # 简单的复数处理
        if word.endswith('s') and len(word) > 3:
            # 避免过度处理，只处理明显的复数
            if word.endswith('ies'):
                return word[:-3] + 'y'
            elif word.endswith('es'):
                return word[:-2]
            elif word.endswith('s'):
                return word[:-1]
        return word

    processor.difficulty_estimator = LocalDummyEstimator()
    processor.lemma_processor = local_lemma_processor

    # 执行处理
    result = processor.process_article_enhanced(
        raw_text=article,
        text_id=2,
        text_title="Potawatomi Ambush"
    )

    # 保存增强数据
    processor.save_enhanced_data(result, output_dir="enhanced_output")

    # 打印简要摘要
    print("\n=== Enhanced Processing Summary ===")
    print(f"Sentences: {result['total_sentences']}")
    print(f"Tokens: {result['total_tokens']}")
    print(f"Vocab generated: {len(result.get('vocab_expressions', []))}")
    if result.get('vocab_expressions'):
        first = result['vocab_expressions'][0]
        print(f"Example Vocab: id={first.get('vocab_id')}, body='{first.get('vocab_body')}', examples={len(first.get('examples', []))}")

if __name__ == "__main__":
    main() 