from src.core.sentence_splitter import read_and_split_sentences
from src.core.token_splitter import split_tokens

def final_demo():
    """
    最终演示：展示句子分割器和token分割器的功能
    """
    print("=== 文本处理工具集演示 ===\n")
    
    # 测试文件
    test_file = "test_text.txt"
    
    print("1. 句子分割器演示:")
    print("=" * 50)
    
    # 读取并分割句子
    sentences = read_and_split_sentences(test_file)
    
    if sentences:
        print(f"从文件 '{test_file}' 中读取到 {len(sentences)} 个句子：\n")
        for i, sentence in enumerate(sentences, 1):
            print(f"句子 {i}: {sentence}")
        print()
    
    print("2. Token分割器演示:")
    print("=" * 50)
    
    # 对每个句子进行token分割
    for i, sentence in enumerate(sentences, 1):
        print(f"\n句子 {i}: '{sentence}'")
        tokens = split_tokens(sentence)
        print(f"Tokens ({len(tokens)}): {tokens}")
    
    print("\n" + "=" * 50)
    print("演示完成！")

if __name__ == "__main__":
    final_demo() 