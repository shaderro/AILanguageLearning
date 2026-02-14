#!/usr/bin/env python3
"""
手动测试 SummarizeGrammarRuleAssistant 的脚本。

前置条件：
- 已在项目根目录运行（与 backend 同级）
- 已在 .env 或系统环境变量中配置 OPENAI_API_KEY（DeepSeek 代理）
"""

from typing import Optional

from backend.assistants.sub_assistants.summarize_grammar_rule import (
    SummarizeGrammarRuleAssistant,
)


def run_single_test(
    *,
    quoted_sentence: str,
    user_question: str,
    ai_response: str,
    dialogue_context: Optional[str] = None,
    language: str = "中文",
) -> None:
    """
    运行一次 summarize_grammar_assistant，并打印结果。
    """
    assistant = SummarizeGrammarRuleAssistant()

    print("=" * 80)
    print("🔍 测试 SummarizeGrammarRuleAssistant")
    print(f"- language       : {language}")
    print(f"- quoted_sentence: {quoted_sentence}")
    print(f"- user_question  : {user_question}")
    print(f"- ai_response    : {ai_response}")
    if dialogue_context:
        print(f"- dialogue_context: {dialogue_context}")
    print("=" * 80)

    # 注意：这里只是功能测试，不记录 token，不传 user_id / session
    result = assistant.run(
        quoted_sentence=quoted_sentence,
        user_question=user_question,
        ai_response=ai_response,
        dialogue_context=dialogue_context,
        language=language,
        verbose=True,
    )

    print("\n📤 原始返回结果类型:", type(result))
    print("📤 原始返回结果内容:", result)

    # 尝试按我们期望的新结构解读
    print("\n📊 解析为 display_name / canonical：")

    def _print_item(item, idx: Optional[int] = None) -> None:
        prefix = f"[{idx}] " if idx is not None else ""
        if not isinstance(item, dict):
            print(f"{prefix}⚠️ 非 dict，原样输出:", item)
            return
        display_name = item.get("display_name")
        canonical = item.get("canonical") or {}
        category = canonical.get("category")
        subtype = canonical.get("subtype")
        function = canonical.get("function")
        print(
            f"{prefix}display_name={display_name!r}, "
            f"category={category!r}, subtype={subtype!r}, function={function!r}"
        )

    if isinstance(result, dict):
        if "result" in result and result["result"] is None:
            print("➡️ result: null （无明确语法结构）")
        else:
            _print_item(result)
    elif isinstance(result, list):
        if not result:
            print("➡️ 空列表")
        else:
            for i, item in enumerate(result):
                _print_item(item, i)
    else:
        print("⚠️ 返回既不是 dict 也不是 list，可能是原始字符串：", result)


def main() -> None:
    """
    在这里手动设置测试用例。
    可以根据需要修改/增加不同语言和不同句子的测试。
    """
    # 示例 1：中文，定语从句
    run_single_test(
        quoted_sentence="这是我昨天买的书。",
        user_question="这句话里的语法结构是什么？",
        ai_response="这里用了定语从句，“我昨天买的”这个从句修饰前面的“书”。",
        dialogue_context="我们在讨论表示“这本书”的不同说法。",
        language="中文",
    )

    # 示例 2：英文，被动语态
    run_single_test(
        quoted_sentence="The book was written by him.",
        user_question="这里用了什么语法？",
        ai_response="这是一般过去时的被动语态结构：was written。",
        dialogue_context=None,
        language="中文",
    )


if __name__ == "__main__":
    main()


