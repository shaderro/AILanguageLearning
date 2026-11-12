#!/usr/bin/env python3
"""
OpenAI使用示例脚本
演示如何在项目中使用OpenAI API
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.openai_utils import OpenAIHelper, test_openai_connection
from src.core.token_splitter import split_tokens
from src.utils.get_lemma import get_lemma
from src.utils.get_pos_tag import get_pos_tag

def setup_environment():
    """设置环境变量（如果还没有设置）"""
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  请设置OPENAI_API_KEY环境变量")
        print("方法1: 在命令行中运行: set OPENAI_API_KEY=your_api_key_here")
        print("方法2: 在代码中设置: os.environ['OPENAI_API_KEY'] = 'your_api_key_here'")
        return False
    return True

def analyze_text_with_openai():
    """使用OpenAI分析文本"""
    print("\n=== 文本分析示例 ===")
    
    text = "The quick brown fox jumps over the lazy dog. This sentence contains all the letters of the alphabet."
    
    try:
        helper = OpenAIHelper()
        
        # 分析文本难度
        print("分析文本难度...")
        difficulty_analysis = helper.analyze_text(text, "difficulty")
        print(f"难度分析: {difficulty_analysis}")
        
        # 分析语法
        print("\n分析语法...")
        grammar_analysis = helper.analyze_text(text, "grammar")
        print(f"语法分析: {grammar_analysis}")
        
    except Exception as e:
        print(f"分析失败: {e}")

def analyze_tokens_with_openai():
    """使用OpenAI分析token"""
    print("\n=== Token分析示例 ===")
    
    text = "Although the weather was terrible, we still enjoyed our vacation."
    
    try:
        # 分割tokens
        tokens = split_tokens(text)
        print(f"分割得到 {len(tokens)} 个tokens:")
        
        helper = OpenAIHelper()
        
        for i, token in enumerate(tokens[:5], 1):  # 只分析前5个token
            token_body = token['token_body']
            token_type = token['token_type']
            
            print(f"\n{i}. Token: '{token_body}' (类型: {token_type})")
            
            if token_type == "text":
                # 获取lemma
                lemma = get_lemma(token_body)
                print(f"   Lemma: {lemma}")
                
                # 获取POS标签
                pos_tag = get_pos_tag(token_body)
                print(f"   POS: {pos_tag}")
                
                # 使用OpenAI分析难度
                difficulty_info = helper.get_token_difficulty(token_body, text)
                print(f"   OpenAI难度分析: {difficulty_info.get('raw_response', 'N/A')}")
                
    except Exception as e:
        print(f"Token分析失败: {e}")

def interactive_openai_chat():
    """交互式OpenAI聊天"""
    print("\n=== 交互式OpenAI聊天 ===")
    print("输入问题与AI对话，输入 'quit' 退出")
    
    try:
        helper = OpenAIHelper()
        
        while True:
            user_input = input("\n您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("聊天结束。")
                break
            
            if not user_input:
                continue
            
            try:
                response = helper.chat_completion([
                    {"role": "user", "content": user_input}
                ])
                print(f"AI: {response}")
            except Exception as e:
                print(f"AI回复失败: {e}")
                
    except Exception as e:
        print(f"聊天初始化失败: {e}")

def main():
    """主函数"""
    print("🚀 OpenAI项目集成示例")
    print("=" * 50)
    
    # 检查环境设置
    if not setup_environment():
        return
    
    # 测试连接
    print("测试OpenAI连接...")
    if not test_openai_connection():
        print("❌ 无法连接到OpenAI，请检查API密钥和网络连接")
        return
    
    print("✅ OpenAI连接成功！")
    
    # 运行示例
    while True:
        print("\n请选择要运行的示例:")
        print("1. 文本分析")
        print("2. Token分析")
        print("3. 交互式聊天")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == '1':
            analyze_text_with_openai()
        elif choice == '2':
            analyze_tokens_with_openai()
        elif choice == '3':
            interactive_openai_chat()
        elif choice == '4':
            print("再见！")
            break
        else:
            print("无效选择，请重新输入。")

if __name__ == "__main__":
    main() 