import re
import json
import os
from typing import List, Union
from .token_data import OriginalText, Sentence, Token
from .token_splitter import split_tokens

def split_sentences(text: str) -> List[str]:
    """
    将文本按句子分隔
    使用正则表达式匹配句号、问号、感叹号作为句子结束标记
    """
    # 使用正则表达式分割句子
    # 匹配句号、问号、感叹号，后面跟着空格或换行符
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # 过滤掉空字符串并去除首尾空白
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    
    return sentences

def read_and_split_sentences(file_path: str) -> List[str]:
    """
    读取txt文件并返回分割后的句子列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        sentences = split_sentences(content)
        return sentences
    
    except FileNotFoundError:
        print(f"错误：找不到文件 '{file_path}'")
        return []
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return []

def process_text_to_structured_data(text: Union[str, str], text_id: int, text_title: str = "") -> OriginalText:
    """
    将文本处理成结构化数据
    
    Args:
        text: 文本内容或文件路径
        text_id: 文本ID
        text_title: 文本标题
        
    Returns:
        OriginalText: 结构化的文本数据
    """
    # 如果输入是文件路径，先读取文件
    if os.path.isfile(text):
        with open(text, 'r', encoding='utf-8') as file:
            text_content = file.read()
        if not text_title:
            text_title = os.path.basename(text)
    else:
        text_content = text
        if not text_title:
            text_title = f"Text_{text_id}"
    
    # 分割句子
    sentence_texts = split_sentences(text_content)
    
    # 创建句子对象列表
    sentences = []
    global_token_id = 0
    
    for sentence_id, sentence_text in enumerate(sentence_texts, 1):
        # 分割tokens
        token_dicts = split_tokens(sentence_text)
        
        # 创建Token对象列表
        tokens = []
        for token_id, token_dict in enumerate(token_dicts, 1):
            token = Token(
                token_body=token_dict["token_body"],
                token_type=token_dict["token_type"],
                global_token_id=global_token_id,
                sentence_token_id=token_id
            )
            tokens.append(token)
            global_token_id += 1
        
        # 创建Sentence对象
        sentence = Sentence(
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_body=sentence_text,
            grammar_annotations=[],
            vocab_annotations=[],
            tokens=tokens
        )
        sentences.append(sentence)
    
    # 创建OriginalText对象
    original_text = OriginalText(
        text_id=text_id,
        text_title=text_title,
        text_by_sentence=sentences
    )
    
    return original_text

def save_structured_data(original_text: OriginalText, output_dir: str):
    """
    保存结构化数据到指定目录
    
    Args:
        original_text: 结构化的文本数据
        output_dir: 输出目录路径
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存original_text.json
    original_text_data = {
        "text_id": original_text.text_id,
        "text_title": original_text.text_title,
        "text_by_sentence": [
            {
                "text_id": sentence.text_id,
                "sentence_id": sentence.sentence_id,
                "sentence_body": sentence.sentence_body,
                "grammar_annotations": sentence.grammar_annotations,
                "vocab_annotations": sentence.vocab_annotations,
                "tokens": [
                    {
                        "token_body": token.token_body,
                        "token_type": token.token_type,
                        "difficulty_level": token.difficulty_level,
                        "global_token_id": token.global_token_id,
                        "sentence_token_id": token.sentence_token_id,
                        "linked_vocab_id": token.linked_vocab_id,
                        "pos_tag": token.pos_tag,
                        "lemma": token.lemma,
                        "is_grammar_marker": token.is_grammar_marker
                    }
                    for token in sentence.tokens
                ]
            }
            for sentence in original_text.text_by_sentence
        ]
    }
    
    with open(os.path.join(output_dir, "original_text.json"), 'w', encoding='utf-8') as f:
        json.dump(original_text_data, f, ensure_ascii=False, indent=2)
    
    # 保存sentences.json
    sentences_data = [
        {
            "text_id": sentence.text_id,
            "sentence_id": sentence.sentence_id,
            "sentence_body": sentence.sentence_body,
            "grammar_annotations": sentence.grammar_annotations,
            "vocab_annotations": sentence.vocab_annotations,
            "tokens": [
                {
                    "token_body": token.token_body,
                    "token_type": token.token_type,
                    "difficulty_level": token.difficulty_level,
                    "global_token_id": token.global_token_id,
                    "sentence_token_id": token.sentence_token_id,
                    "linked_vocab_id": token.linked_vocab_id,
                    "pos_tag": token.pos_tag,
                    "lemma": token.lemma,
                    "is_grammar_marker": token.is_grammar_marker
                }
                for token in sentence.tokens
            ]
        }
        for sentence in original_text.text_by_sentence
    ]
    
    with open(os.path.join(output_dir, "sentences.json"), 'w', encoding='utf-8') as f:
        json.dump(sentences_data, f, ensure_ascii=False, indent=2)
    
    # 保存tokens.json (所有tokens的扁平化列表)
    all_tokens = []
    for sentence in original_text.text_by_sentence:
        for token in sentence.tokens:
            all_tokens.append({
                "token_body": token.token_body,
                "token_type": token.token_type,
                "difficulty_level": token.difficulty_level,
                "global_token_id": token.global_token_id,
                "sentence_token_id": token.sentence_token_id,
                "sentence_id": sentence.sentence_id,
                "text_id": sentence.text_id,
                "linked_vocab_id": token.linked_vocab_id,
                "pos_tag": token.pos_tag,
                "lemma": token.lemma,
                "is_grammar_marker": token.is_grammar_marker
            })
    
    with open(os.path.join(output_dir, "tokens.json"), 'w', encoding='utf-8') as f:
        json.dump(all_tokens, f, ensure_ascii=False, indent=2)

def process_text_file(input_path: str, text_id: int, output_dir: str = None):
    """
    处理文本文件并保存结构化数据
    
    Args:
        input_path: 输入文件路径
        text_id: 文本ID
        output_dir: 输出目录路径，如果为None则使用默认路径
    """
    if output_dir is None:
        output_dir = f"data/text_{text_id:03d}"
    
    # 处理文本
    original_text = process_text_to_structured_data(input_path, text_id)
    
    # 保存数据
    save_structured_data(original_text, output_dir)
    
    print(f"✅ 文本处理完成！")
    print(f"📁 输出目录: {output_dir}")
    print(f"📄 句子数量: {len(original_text.text_by_sentence)}")
    print(f"🔤 总token数量: {sum(len(sentence.tokens) for sentence in original_text.text_by_sentence)}")

def main():
    # 测试文件路径
    test_file = "test_text.txt"
    
    print("正在读取文件并分割句子...")
    sentences = read_and_split_sentences(test_file)
    
    if sentences:
        print(f"\n共找到 {len(sentences)} 个句子：\n")
        for i, sentence in enumerate(sentences, 1):
            print(f"{i}. {sentence}")
    else:
        print("没有找到句子或文件读取失败")

if __name__ == "__main__":
    main() 