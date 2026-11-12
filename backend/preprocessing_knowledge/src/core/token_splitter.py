import re
from typing import List, Dict, Any

def split_tokens(text: str) -> List[Dict[str, Any]]:
    """
    将文本分割成tokens，按照token_data.py中定义的数据结构
    
    Args:
        text: 输入的文本字符串
        
    Returns:
        List[Dict[str, Any]]: 包含token_body和token_type的token列表
    """
    if not text:
        return []
    
    tokens = []
    
    # 使用正则表达式匹配不同类型的token
    # 匹配单词（包括连字符、撇号等）
    word_pattern = r'\b[\w\'-]+\b'
    # 匹配标点符号
    punctuation_pattern = r'[^\w\s]'
    # 匹配空白字符
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
            continue  # 跳过不匹配的情况
        
        # 创建token字典，只包含前两项
        token = {
            "token_body": token_body,
            "token_type": token_type
        }
        
        tokens.append(token)
    
    return tokens

def main():
    """
    主函数：用于测试token分割功能
    """
    print("=== 新的Token Splitter ===")
    print("输入文本，程序将按照token.py中的数据结构分割tokens")
    print("输出只包含token_body和token_type")
    print("输入 'quit' 或 'exit' 退出程序\n")
    
    while True:
        try:
            # 获取用户输入
            text = input("请输入文本: ").strip()
            
            # 检查退出命令
            if text.lower() in ['quit', 'exit', '退出']:
                print("程序已退出。")
                break
            
            # 检查空输入
            if not text:
                print("请输入有效的文本。\n")
                continue
            
            # 分割tokens
            tokens = split_tokens(text)
            
            # 显示结果
            print(f"\n共找到 {len(tokens)} 个tokens：")
            for i, token in enumerate(tokens, 1):
                print(f"{i:2d}. token_body: '{token['token_body']}', token_type: '{token['token_type']}'")
            
            print()  # 空行分隔
            
        except KeyboardInterrupt:
            print("\n\n程序被用户中断。")
            break
        except Exception as e:
            print(f"处理时发生错误：{e}\n")

if __name__ == "__main__":
    main() 