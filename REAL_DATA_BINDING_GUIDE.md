# 真实数据绑定实现指南

## 概述

本文档说明如何在 `run_main_ui` 的主程序中绑定真实的语法和词汇数据，替换原有的硬编码数据。

## 实现内容

### 1. 数据管理器初始化

在 `MainScreen` 的 `__init__` 方法中添加了数据管理器初始化：

```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.swipe_handler = SwipeHandler()
    
    # Initialize ViewModel
    self.article_viewmodel = ArticleListViewModel()
    
    # Initialize data managers for real grammar and vocabulary data
    self.grammar_manager = None
    self.vocab_manager = None
    self._initialize_data_managers()
    
    # Store card references
    self.article_cards = []
    self.vocab_cards = []
```

### 2. 数据管理器初始化方法

新增 `_initialize_data_managers` 方法：

```python
def _initialize_data_managers(self):
    """Initialize grammar and vocabulary data managers"""
    try:
        print("📚 Initializing data managers for real grammar and vocabulary data...")
        
        # Import data managers
        from data_managers.grammar_rule_manager import GrammarRuleManager
        from data_managers.vocab_manager import VocabManager
        
        # Create managers
        self.grammar_manager = GrammarRuleManager()
        self.vocab_manager = VocabManager()
        
        # Load data from files
        try:
            self.grammar_manager.load_from_file("data/grammar_rules.json")
            print(f"✅ Loaded {len(self.grammar_manager.grammar_bundles)} grammar rules")
        except Exception as e:
            print(f"⚠️ Failed to load grammar rules: {e}")
        
        try:
            self.vocab_manager.load_from_file("data/vocab_expressions.json")
            print(f"✅ Loaded {len(self.vocab_manager.vocab_bundles)} vocabulary expressions")
        except Exception as e:
            print(f"⚠️ Failed to load vocabulary expressions: {e}")
        
    except Exception as e:
        print(f"❌ Error initializing data managers: {e}")
        self.grammar_manager = None
        self.vocab_manager = None
```

### 3. 真实语法数据绑定

修改 `show_grammar_content` 方法：

```python
def show_grammar_content(self, *args):
    """Show grammar content with real data"""
    self.sub_tab1_btn.set_active(True)
    self.sub_tab2_btn.set_active(False)
    
    # Clear container
    self.learn_container.clear_widgets()
    
    if self.grammar_manager and self.grammar_manager.grammar_bundles:
        # Use real grammar data
        print(f"📚 Loading {len(self.grammar_manager.grammar_bundles)} grammar rules...")
        
        for rule_id, bundle in self.grammar_manager.grammar_bundles.items():
            rule = bundle.rule
            examples = bundle.examples
            
            # Get example sentence if available
            example_text = "No example available"
            if examples:
                # Use the first example
                example = examples[0]
                # Try to get the sentence from text manager
                try:
                    from data_managers.original_text_manager import OriginalTextManager
                    text_manager = OriginalTextManager()
                    text_manager.load_from_file("data/original_texts.json")
                    sentence = text_manager.get_sentence_by_id(example.text_id, example.sentence_id)
                    if sentence:
                        example_text = sentence.sentence_body
                except Exception as e:
                    print(f"⚠️ Could not load example sentence: {e}")
            
            # Determine difficulty based on rule complexity
            difficulty = self._determine_grammar_difficulty(rule.explanation)
            
            # Create grammar card
            card = VocabCard(
                rule.name,
                rule.explanation,
                example_text,
                difficulty,
                on_press_callback=partial(self.open_grammar_detail, rule.name, rule.explanation, example_text, difficulty)
            )
            self.learn_container.add_widget(card)
            print(f"📝 Added grammar card: {rule.name}")
    else:
        # Fallback to hardcoded data if no real data available
        print("⚠️ No real grammar data available, using fallback data")
        # ... fallback code ...
```

### 4. 真实词汇数据绑定

修改 `show_vocab_content` 方法：

```python
def show_vocab_content(self, *args):
    """Show vocabulary content with real data"""
    self.sub_tab1_btn.set_active(False)
    self.sub_tab2_btn.set_active(True)
    
    # Clear container
    self.learn_container.clear_widgets()
    
    if self.vocab_manager and self.vocab_manager.vocab_bundles:
        # Use real vocabulary data
        print(f"📚 Loading {len(self.vocab_manager.vocab_bundles)} vocabulary expressions...")
        
        for vocab_id, bundle in self.vocab_manager.vocab_bundles.items():
            vocab = bundle.vocab
            examples = bundle.example
            
            # Get example sentence if available
            example_text = "No example available"
            if examples:
                # Use the first example
                example = examples[0]
                # Try to get the sentence from text manager
                try:
                    from data_managers.original_text_manager import OriginalTextManager
                    text_manager = OriginalTextManager()
                    text_manager.load_from_file("data/original_texts.json")
                    sentence = text_manager.get_sentence_by_id(example.text_id, example.sentence_id)
                    if sentence:
                        example_text = sentence.sentence_body
                except Exception as e:
                    print(f"⚠️ Could not load example sentence: {e}")
            
            # Determine difficulty based on vocabulary complexity
            difficulty = self._determine_vocab_difficulty(vocab.vocab_body, vocab.explanation)
            
            # Create vocabulary card
            card = VocabCard(
                vocab.vocab_body,
                vocab.explanation,
                example_text,
                difficulty,
                on_press_callback=partial(self.open_vocab_detail, vocab.vocab_body, vocab.explanation, example_text, difficulty)
            )
            self.learn_container.add_widget(card)
            print(f"📝 Added vocabulary card: {vocab.vocab_body}")
    else:
        # Fallback to hardcoded data if no real data available
        print("⚠️ No real vocabulary data available, using fallback data")
        # ... fallback code ...
```

### 5. 难度判断方法

新增难度判断方法：

```python
def _determine_grammar_difficulty(self, explanation):
    """Determine grammar rule difficulty based on explanation"""
    # Simple heuristic based on explanation length and complexity
    if len(explanation) < 50:
        return "easy"
    elif len(explanation) < 100:
        return "medium"
    else:
        return "hard"

def _determine_vocab_difficulty(self, vocab_body, explanation):
    """Determine vocabulary difficulty based on word and explanation"""
    # Simple heuristic based on word length and explanation complexity
    if len(vocab_body) <= 5 and len(explanation) < 50:
        return "easy"
    elif len(vocab_body) <= 8 and len(explanation) < 100:
        return "medium"
    else:
        return "hard"
```

### 6. VocabCard组件增强

修改 `VocabCard` 组件以支持回调函数：

```python
class VocabCard(BaseCard):
    """Vocabulary card"""
    
    def __init__(self, word, meaning, example, difficulty, on_press_callback=None, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=8, 
                        size_hint_y=None, height=120, **kwargs)
        
        self.on_press_callback = on_press_callback
        
        # ... existing code ...
    
    def on_press(self):
        """Handle press event"""
        if self.on_press_callback:
            self.on_press_callback()
```

## 数据来源

### 语法数据
- **文件**: `data/grammar_rules.json`
- **结构**: 包含语法规则和例句
- **示例数据**:
  - 副词currently的用法
  - 定语从句in which的用法
  - 主谓一致
  - 连接词sowie的用法
  - 介词与冠词的合写形式
  - 介词Bei的用法
  - 过去分词被动态

### 词汇数据
- **文件**: `data/vocab_expressions.json`
- **结构**: 包含词汇和例句
- **示例数据**:
  - in which
  - encyclopedia
  - free content
  - sowie
  - recording
  - einwohner
  - teilfunktionen

## 功能特性

### 1. 真实数据加载
- 自动从JSON文件加载语法和词汇数据
- 支持错误处理和回退机制
- 实时显示加载状态

### 2. 例句关联
- 自动关联语法规则和词汇的例句
- 从原始文本中提取完整句子
- 处理例句加载失败的情况

### 3. 难度评估
- 基于规则复杂度的语法难度评估
- 基于词汇长度和解释复杂度的词汇难度评估
- 动态难度标签显示

### 4. 交互功能
- 卡片点击事件处理
- 导航到详细信息页面
- 回调函数支持

### 5. 错误处理
- 数据文件不存在时的回退机制
- 例句加载失败时的默认显示
- 详细的错误日志输出

## 测试验证

### 运行测试
```bash
python3 test_real_data_binding.py
```

### 测试要点
1. **数据加载验证**：
   - 检查控制台输出中的加载信息
   - 验证语法和词汇数量是否正确

2. **界面显示验证**：
   - 点击"Learn"标签页
   - 查看"Grammar"子标签中的语法卡片
   - 查看"Vocabulary"子标签中的词汇卡片

3. **数据内容验证**：
   - 检查卡片显示的规则名称和解释
   - 验证例句是否正确显示
   - 确认难度标签是否合理

4. **交互功能验证**：
   - 点击卡片测试回调功能
   - 验证导航是否正常工作

## 文件变更

### 修改的文件
- `ui/screens/main_screen.py` - 添加真实数据绑定
- `ui/components/cards.py` - 增强VocabCard组件

### 新增的文件
- `test_real_data_binding.py` - 测试脚本
- `REAL_DATA_BINDING_GUIDE.md` - 本文档

### 相关数据文件
- `data/grammar_rules.json` - 语法规则数据
- `data/vocab_expressions.json` - 词汇表达式数据
- `data/original_texts.json` - 原始文本数据

## 注意事项

1. **数据文件依赖**：确保数据文件存在且格式正确
2. **错误处理**：系统会自动回退到硬编码数据
3. **性能考虑**：大量数据可能影响加载速度
4. **数据更新**：修改数据文件后需要重启应用
5. **编码问题**：确保JSON文件使用UTF-8编码

## 扩展建议

1. **数据缓存**：实现数据缓存机制提高性能
2. **动态更新**：支持运行时数据更新
3. **搜索功能**：添加语法和词汇搜索功能
4. **分类显示**：按难度或主题分类显示
5. **用户进度**：记录用户学习进度 