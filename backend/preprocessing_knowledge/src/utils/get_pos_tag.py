import nltk
from typing import Optional

# 下载必要的NLTK数据（如果还没有下载的话）
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("正在下载POS tagger数据...")
    nltk.download('averaged_perceptron_tagger')

def get_pos_tag(token_body: str) -> Optional[str]:
    """
    获取token的POS标签
    
    Args:
        token_body: token的内容
        
    Returns:
        Optional[str]: POS标签，如果无法获取则返回None
    """
    if not token_body or not token_body.strip():
        return None
    
    try:
        # 使用NLTK的POS tagger获取词性标签
        pos_tags = nltk.pos_tag([token_body])
        
        if pos_tags:
            return pos_tags[0][1]  # 返回POS标签
        else:
            return None
            
    except Exception as e:
        print(f"处理token '{token_body}' 时发生错误: {e}")
        return None

def get_pos_tag_description(pos_tag: str) -> str:
    """
    获取POS标签的描述
    
    Args:
        pos_tag: POS标签
        
    Returns:
        str: POS标签的描述
    """
    pos_descriptions = {
        # 名词
        'NN': '名词，单数',
        'NNS': '名词，复数',
        'NNP': '专有名词，单数',
        'NNPS': '专有名词，复数',
        
        # 动词
        'VB': '动词，原形',
        'VBD': '动词，过去式',
        'VBG': '动词，现在分词',
        'VBN': '动词，过去分词',
        'VBP': '动词，非第三人称单数现在式',
        'VBZ': '动词，第三人称单数现在式',
        
        # 形容词
        'JJ': '形容词',
        'JJR': '形容词，比较级',
        'JJS': '形容词，最高级',
        
        # 副词
        'RB': '副词',
        'RBR': '副词，比较级',
        'RBS': '副词，最高级',
        
        # 代词
        'PRP': '人称代词',
        'PRP$': '所有格代词',
        'WP': '疑问代词',
        'WP$': '所有格疑问代词',
        
        # 限定词
        'DT': '限定词',
        'WDT': '疑问限定词',
        
        # 介词
        'IN': '介词或从属连词',
        
        # 连词
        'CC': '并列连词',
        
        # 感叹词
        'UH': '感叹词',
        
        # 数字
        'CD': '基数词',
        
        # 标点符号
        '.': '句号',
        ',': '逗号',
        ':': '冒号',
        ';': '分号',
        '!': '感叹号',
        '?': '问号',
        '"': '引号',
        "'": '撇号',
        '(': '左括号',
        ')': '右括号',
        
        # 其他
        'TO': 'to',
        'EX': '存在there',
        'FW': '外来词',
        'LS': '列表标记',
        'MD': '情态动词',
        'PDT': '前位限定词',
        'POS': '所有格标记',
        'RP': '小品词',
        'SYM': '符号',
        'WRB': '疑问副词'
    }
    
    return pos_descriptions.get(pos_tag, f'未知标签: {pos_tag}')

def main():
    """
    主函数：交互式输入token并获取POS标签
    """
    print("=== Get POS Tag ===")
    print("输入token，程序将返回其POS标签")
    print("输入 'quit' 或 'exit' 退出程序\n")
    
    while True:
        try:
            # 获取用户输入
            token_body = input("请输入token: ").strip()
            
            # 检查退出命令
            if token_body.lower() in ['quit', 'exit', '退出']:
                print("程序已退出。")
                break
            
            # 检查空输入
            if not token_body:
                print("请输入有效的token。\n")
                continue
            
            # 获取POS标签
            pos_tag = get_pos_tag(token_body)
            
            # 显示结果
            if pos_tag is not None:
                description = get_pos_tag_description(pos_tag)
                print(f"Token: '{token_body}' -> POS: '{pos_tag}' ({description})")
            else:
                print(f"无法获取 '{token_body}' 的POS标签")
            
            print()  # 空行分隔
            
        except KeyboardInterrupt:
            print("\n\n程序被用户中断。")
            break
        except Exception as e:
            print(f"处理时发生错误：{e}\n")

if __name__ == "__main__":
    main() 