import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from typing import Optional
import os

# 下载必要的NLTK数据（如果还没有下载的话）
def ensure_nltk_data():
    """确保NLTK数据已下载"""
    try:
        # 检查wordnet是否可用
        nltk.data.find('corpora/wordnet')
    except LookupError:
        print("正在下载WordNet数据...")
        nltk.download('wordnet', quiet=True)
    
    try:
        # 检查pos_tagger是否可用
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        print("正在下载POS tagger数据...")
        nltk.download('averaged_perceptron_tagger', quiet=True)

# 确保数据已下载
ensure_nltk_data()

def get_wordnet_pos(word: str) -> str:
    """
    获取单词的词性标签，用于lemmatization
    
    Args:
        word: 输入的单词
        
    Returns:
        str: WordNet词性标签
    """
    try:
        # 获取单词的词性
        tag = nltk.pos_tag([word])[0][1]
        
        # 将Penn Treebank词性标签转换为WordNet词性标签
        tag_dict = {
            "J": wordnet.ADJ,
            "N": wordnet.NOUN,
            "V": wordnet.VERB,
            "R": wordnet.ADV
        }
        
        return tag_dict.get(tag[0], wordnet.NOUN)
    except Exception as e:
        # 如果POS tagging失败，返回默认的NOUN
        return wordnet.NOUN

def get_lemma(token_body: str) -> Optional[str]:
    """
    获取text类token的lemma形式
    
    Args:
        token_body: text类token的内容
        
    Returns:
        Optional[str]: lemma形式，如果无法获取则返回None
    """
    if not token_body or not token_body.strip():
        return None
    
    # 清理token，移除标点符号
    clean_token = token_body.strip().lower()
    
    # 如果token只包含标点符号或数字，返回None
    if not clean_token.isalpha():
        return None
    
    try:
        # 创建lemmatizer
        lemmatizer = WordNetLemmatizer()
        
        # 获取词性
        pos = get_wordnet_pos(clean_token)
        
        # 获取lemma
        lemma = lemmatizer.lemmatize(clean_token, pos)
        
        return lemma
        
    except Exception as e:
        # 静默处理错误，返回None而不是打印错误信息
        return None

def main():
    """
    主函数：交互式输入text类token并获取lemma
    """
    print("=== Get Lemma ===")
    print("输入text类token，程序将返回其lemma形式")
    print("输入 'quit' 或 'exit' 退出程序\n")
    
    while True:
        try:
            # 获取用户输入
            token_body = input("请输入text类token: ").strip()
            
            # 检查退出命令
            if token_body.lower() in ['quit', 'exit', '退出']:
                print("程序已退出。")
                break
            
            # 检查空输入
            if not token_body:
                print("请输入有效的token。\n")
                continue
            
            # 获取lemma
            lemma = get_lemma(token_body)
            
            # 显示结果
            if lemma is not None:
                print(f"Token: '{token_body}' -> Lemma: '{lemma}'")
            else:
                print(f"无法获取 '{token_body}' 的lemma形式")
            
            print()  # 空行分隔
            
        except KeyboardInterrupt:
            print("\n\n程序被用户中断。")
            break
        except Exception as e:
            print(f"处理时发生错误：{e}\n")

if __name__ == "__main__":
    main() 