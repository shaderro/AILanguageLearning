import json
import re
import ast


def parse_json_from_text(text):
    try:
        text = text.strip()
        # 自动移除包裹双花括号的形式
        if text.startswith("{{") and text.endswith("}}"):
            text = text[1:-1].strip()  # 去掉外层的大括号
        
        # 移除 Markdown 代码块
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.IGNORECASE).strip()
        
        # 匹配第一个 JSON 对象
        match = re.search(r'\{[\s\S]*?\}', text)
        if not match:
            raise ValueError("未找到 JSON 对象")
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 尝试用 ast.literal_eval 解析 Python 字典字符串
            return ast.literal_eval(json_str)
    except Exception as e:
        print("❗️解析 JSON 失败：", e)
        print("🪵 原始模型输出：", text)
        return None
    
test_string = "{\"grammar_rule_name\": \"定语从句中的in which\",\"grammar_rule_summary\": \"in which相当于where，用于引导定语从句，表示‘在其中’，which指代前面提到的名词\"}"
result = parse_json_from_text(test_string)
print(result)
print(type(result))