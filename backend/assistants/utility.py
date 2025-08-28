import json
import re
import ast


def parse_json_from_text(text):
    try:
        text = text.strip()

        # 自动移除包裹双花括号的形式
        if text.startswith("{{") and text.endswith("}}"):
            text = text[1:-1].strip()

        # 移除 Markdown 代码块
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.IGNORECASE).strip()

        # 尝试整体作为 JSON 解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试用 ast.literal_eval 解析 Python 字典/列表字符串
            return ast.literal_eval(text)

    except Exception as e:
        print("❗️解析 JSON 失败：", e)
        print("🪵 原始模型输出：", text)
        return None
    
    """
    test_string = '''[
    {
        "grammar_rule_name": "定语从句in which",
        "grammar_rule_summary": "in which相当于where，用于引导定语从句，表示‘在其中’，which指代前面提到的名词"
    },
    {
        "grammar_rule_name": "关系代词which引导的定语从句",
        "grammar_rule_summary": "关系代词which可以引导定语从句，指代前面的名词（这里是online encyclopedia website），并在从句中充当主语或宾语。当which指代复数名词时，从句中的谓语动词要用复数形式（如are）。"
    }
]'''
result = parse_json_from_text(test_string)
print(result)
print(type(result))
    """
