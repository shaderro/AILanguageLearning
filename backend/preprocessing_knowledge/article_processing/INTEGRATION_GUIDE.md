# 文章处理模块集成指南

## 📋 概述

本文档说明如何将 `article_processing` 模块集成到你的主项目中，特别是如何集成 `single token difficulty estimation` 和 `vocab explanation` 功能。

## 🔧 当前状态

### ✅ 已完成的功能
- 句子分割 (`split_sentences`)
- Token分割 (`split_tokens`)
- 基本数据结构创建
- 数据保存功能

### ❌ 需要集成的功能
- Single Token Difficulty Estimation
- Vocab Explanation
- Lemma 获取
- POS Tag 标注

## 🚀 集成步骤

### 步骤1: 复制模块到主项目

将 `article_processing` 文件夹复制到你的主项目中：

```bash
cp -r article_processing /path/to/your/main/project/
```

### 步骤2: 修改导入路径

在 `enhanced_processor.py` 中，需要根据你的主项目结构调整导入路径：

#### 2.1 难度评估器导入

```python
# 在 _init_difficulty_estimator 方法中
def _init_difficulty_estimator(self):
    """初始化难度评估器"""
    try:
        # 根据你的项目结构调整路径
        from your_project.agents.single_token_difficulty_estimation import SingleTokenDifficultyEstimator
        self.difficulty_estimator = SingleTokenDifficultyEstimator()
    except ImportError as e:
        print(f"❌ 无法导入难度评估器: {e}")
        self.enable_difficulty_estimation = False

def _init_lemma_processor(self):
    """初始化lemma处理器"""
    try:
        # 根据你的项目结构调整路径
        from your_project.utils.get_lemma import get_lemma
        self.lemma_processor = get_lemma
    except ImportError as e:
        print(f"❌ 无法导入lemma处理器: {e}")
        self.lemma_processor = None
```

#### 2.2 词汇转换器导入

```python
# 在 _init_vocab_converter 方法中
def _init_vocab_converter(self):
    """初始化词汇转换器"""
    try:
        # 根据你的项目结构调整路径
        from your_project.utils.token_to_vocab import TokenToVocabConverter
        vocab_data_file = os.path.join(self.output_base_dir, "vocab_data.json")
        self.vocab_converter = TokenToVocabConverter(vocab_data_file)
    except ImportError as e:
        print(f"❌ 无法导入词汇转换器: {e}")
        self.enable_vocab_explanation = False
```

#### 2.3 Lemma 功能导入

```python
# 在 get_token_lemma 方法中（已集成到处理器中）
def get_token_lemma(self, token_body: str) -> Optional[str]:
    """获取token的lemma形式"""
    if not self.lemma_processor:
        return None
        
    try:
        # 只对text类型的token进行lemma处理
        if not token_body or not token_body.strip():
            return None
        
        # 调用lemma处理器
        lemma = self.lemma_processor(token_body)
        return lemma
        
    except Exception as e:
        print(f"❌ 获取token '{token_body}' 的lemma时发生错误: {e}")
        return None
```

### 步骤3: 使用增强版处理器

```python
from article_processing.enhanced_processor import EnhancedArticleProcessor

# 创建处理器
processor = EnhancedArticleProcessor(output_base_dir="data")

# 启用高级功能
processor.enable_advanced_features(
    enable_difficulty=True,  # 启用难度评估
    enable_vocab=True        # 启用词汇解释
)

# 处理文章
result = processor.process_article_enhanced(
    raw_text="Your article text here...",
    text_id=1,
    text_title="My Article"
)

# 保存数据
processor.save_enhanced_data(result, "output_data")
```

## 📊 输出格式

### 基础输出
```json
{
  "text_id": 1,
  "text_title": "My Article",
  "sentences": [...],
  "total_sentences": 5,
  "total_tokens": 120
}
```

### 增强输出（启用高级功能后）
```json
{
  "text_id": 1,
  "text_title": "My Article",
  "sentences": [...],
  "total_sentences": 5,
  "total_tokens": 120,
  "vocab_expressions": [...]
}
```

### Token 增强字段
```json
{
  "token_body": "artificial",
  "token_type": "text",
  "difficulty_level": "hard",
  "global_token_id": 0,
  "sentence_token_id": 1,
  "linked_vocab_id": 1,
  "pos_tag": "JJ",
  "lemma": "artificial",
  "is_grammar_marker": false
}
```

## 🔗 依赖关系

### 必需依赖
- `src/agents/single_token_difficulty_estimation.py`
- `src/utils/token_to_vocab.py`
- `src/utils/get_lemma.py`
- `src/core/token_data.py` (已存在)

### 可选依赖
- `src/utils/get_pos_tag.py` (用于POS标注)
- `src/agents/grammar_analysis.py` (用于语法分析)

## 🧪 测试集成

### 测试脚本

```python
# test_integration.py
from article_processing.enhanced_processor import EnhancedArticleProcessor

def test_integration():
    # 创建处理器
    processor = EnhancedArticleProcessor()
    
    # 启用所有功能
    processor.enable_advanced_features(True, True)
    
    # 测试文章
    test_article = """
    Artificial intelligence has revolutionized the way we interact with technology. 
    Machine learning algorithms can now process vast amounts of data efficiently.
    """
    
    # 处理文章
    result = processor.process_article_enhanced(
        raw_text=test_article,
        text_id=1,
        text_title="Test Article"
    )
    
    # 验证结果
    print(f"句子数: {result['total_sentences']}")
    print(f"Token数: {result['total_tokens']}")
    print(f"词汇解释数: {len(result.get('vocab_expressions', []))}")
    
    # 检查难度评估
    hard_tokens = 0
    for sentence in result['sentences']:
        for token in sentence['tokens']:
            if token.get('difficulty_level') == 'hard':
                hard_tokens += 1
                print(f"Hard token: {token['token_body']}")
    
    print(f"Hard tokens: {hard_tokens}")

if __name__ == "__main__":
    test_integration()
```

## ⚠️ 注意事项

### 1. 导入路径
确保所有导入路径都正确指向你的主项目结构。

### 2. 依赖检查
在启用高级功能前，确保所有必需的依赖都已正确安装和配置。

### 3. 错误处理
模块包含完善的错误处理机制，如果某个功能无法加载，会自动禁用该功能并继续处理。

### 4. 性能考虑
- 难度评估和词汇解释会增加处理时间
- 建议对大型文档进行分批处理
- 可以考虑添加缓存机制

## 🔄 迁移检查清单

- [ ] 复制 `article_processing` 文件夹到主项目
- [ ] 修改 `enhanced_processor.py` 中的导入路径
- [ ] 确保所有依赖模块可用
- [ ] 测试基础功能（句子分割、token分割）
- [ ] 测试难度评估功能
- [ ] 测试词汇解释功能
- [ ] 验证输出格式
- [ ] 集成到主项目的工作流程中

## 📞 支持

如果在集成过程中遇到问题，请检查：

1. 导入路径是否正确
2. 依赖模块是否可用
3. 项目结构是否匹配
4. 错误日志中的具体信息 