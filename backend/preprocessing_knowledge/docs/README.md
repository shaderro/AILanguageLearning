# 文本处理工具集 (Text Processing Tools)

这个项目包含两个Python脚本，用于文本处理：
1. **句子分割器 (Sentence Splitter)** - 将文本按句子分隔
2. **Token分割器 (Token Splitter)** - 将句子按单词分割，标点符号与前面的单词组合

## 功能特点

### 句子分割器 (sentence_splitter.py)
- 支持读取UTF-8编码的txt文件
- 使用句号(.)、问号(?)、感叹号(!)作为句子分隔符
- 自动过滤空字符串和空白字符
- 包含错误处理机制

### Token分割器 (token_splitter.py)
- 将句子按单词分割
- 标点符号与前面的单词组合成一个token
- 支持连字符单词
- 支持数字和特殊字符
- 交互式输入界面

## 文件说明

- `sentence_splitter.py` - 句子分割脚本
- `token_splitter.py` - Token分割脚本
- `test_text.txt` - 测试用的英文文本文件
- `demo_token_splitter.py` - Token分割器演示脚本
- `simple_test.py` - 简单测试脚本
- `README.md` - 说明文档

## 使用方法

### 句子分割器
```bash
python sentence_splitter.py
```

### Token分割器
```bash
python token_splitter.py
```

或者运行演示：
```bash
python demo_token_splitter.py
```

## 输出示例

### 句子分割器输出
```
正在读取文件并分割句子...

共找到 3 个句子：

1. The quick brown fox jumps over the lazy dog.
2. This is a classic pangram that contains every letter of the English alphabet at least once.
3. Learning to code in Python is both fun and rewarding!
```

### Token分割器输出
```
输入句子: 'Hello, world!'
共找到 2 个tokens：
 1. 'Hello,'
 2. 'world!'
```

## 技术细节

### 句子分割器
- 使用正则表达式 `(?<=[.!?])\s+` 进行句子分割
- 支持多种标点符号作为句子结束标记
- 自动处理文件编码和异常情况

### Token分割器
- 使用正则表达式 `\b[\w-]+\b|[^\w\s]` 匹配单词和标点符号
- 智能处理标点符号与单词的组合
- 支持连字符单词和数字 