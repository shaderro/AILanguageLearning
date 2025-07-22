# Token选择功能指南

## 概述

我已经成功实现了基于词/短语的文本选择功能，限制用户只能选择词或短语，而不是字符级别的任意范围。这大大提升了用户体验和选择的准确性。

## 核心功能

### 1. 分词机制
**位置**：`_tokenize_text()` 方法

**功能**：
- 使用正则表达式将文本分割为词和标点符号
- 保留标点符号作为独立的token
- 过滤空token，确保分词质量

**分词规则**：
```python
# 使用正则表达式分词
tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
```

**示例**：
- 输入：`"The internet has revolutionized the way we learn languages."`
- 输出：`['The', 'internet', 'has', 'revolutionized', 'the', 'way', 'we', 'learn', 'languages', '.']`

### 2. Token显示
**位置**：`_create_article_content()` 方法

**功能**：
- 将每个token显示为独立的Label组件
- 每个token都有独立的背景和点击区域
- 支持自动换行和布局

**显示特性**：
- 字号：48px（放大3倍）
- 每个token独立可点击
- 自动换行处理
- 响应式布局

### 3. 选择机制
**位置**：`_on_token_touch_down()`, `_on_token_touch_move()`, `_on_token_touch_up()` 方法

**功能**：
- 点击选择单个token
- 拖拽选择多个token
- 实时高亮显示选择范围
- 限制选择范围在token级别

**选择流程**：
1. **触摸按下**：开始选择，记录起始token索引
2. **触摸移动**：更新选择范围，实时高亮
3. **触摸抬起**：完成选择，构造选中文本

### 4. 高亮显示
**位置**：`_highlight_token()`, `_highlight_selection_range()` 方法

**功能**：
- 选中token显示蓝色高亮背景
- 未选中token显示白色背景
- 实时更新高亮状态

**视觉效果**：
- 选中：蓝色背景 `(0.2, 0.6, 1, 0.3)`
- 未选中：白色背景 `(1, 1, 1, 1)`

## 技术实现

### 1. 数据结构
```python
# Token相关变量
self.tokens = []                    # 分词结果
self.token_widgets = []             # Token组件列表
self.selection_start_index = -1     # 选择开始索引
self.selection_end_index = -1       # 选择结束索引
self.is_dragging = False            # 拖拽状态
```

### 2. 事件处理
```python
# 绑定事件
token_label.bind(
    pos=self._update_token_bg,
    size=self._update_token_bg,
    on_touch_down=self._on_token_touch_down,
    on_touch_move=self._on_token_touch_move,
    on_touch_up=self._on_token_touch_up
)
```

### 3. 选择逻辑
```python
def _update_selection_from_tokens(self):
    """从token选择更新选择状态"""
    if self.selection_start_index >= 0 and self.selection_end_index >= 0:
        start = min(self.selection_start_index, self.selection_end_index)
        end = max(self.selection_start_index, self.selection_end_index)
        
        # 构造选中的文本
        selected_tokens = []
        for i in range(start, end + 1):
            if 0 <= i < len(self.tokens):
                selected_tokens.append(self.tokens[i])
        
        selected_text = " ".join(selected_tokens)
        self.selected_text_backup = selected_text
        self.is_text_selected = True
```

## 使用方法

### 1. 运行Token选择测试
```bash
python test_token_selection.py
```

### 2. 测试分词逻辑
```bash
python test_tokenization_logic.py
```

### 3. 操作步骤
1. **选择单个词**：点击任意词/短语
2. **选择多个词**：点击起始词，拖拽到结束词
3. **查看选择**：观察选中文本显示区域
4. **输入问题**：点击输入框，选择状态会被保持
5. **发送消息**：输入问题并发送，选中文本会被引用

## 测试结果

### 1. 分词测试 ✅
- 基础分词：通过
- 复杂文本：通过
- 标点符号处理：通过

### 2. 选择逻辑测试 ✅
- 单个token选择：通过
- 多个token选择：通过
- 文本构造：通过

### 3. 功能验证 ✅
- Token显示：正常
- 高亮效果：正常
- 选择保持：正常

## 优势

### 1. 用户体验
- **精确选择**：只能选择完整的词/短语
- **视觉反馈**：清晰的高亮显示
- **操作简单**：点击和拖拽操作直观

### 2. 技术优势
- **性能优化**：基于token的选择比字符选择更高效
- **语义准确**：选择范围符合语言学习需求
- **扩展性强**：易于添加更多选择功能

### 3. 学习效果
- **词汇聚焦**：帮助用户专注于特定词汇
- **短语理解**：支持短语级别的学习
- **上下文保持**：选择范围有明确的语义边界

## 示例场景

### 1. 单词学习
- 选择：`"revolutionized"`
- 问题：`"What does this word mean?"`
- 效果：精确选择单个词汇进行学习

### 2. 短语学习
- 选择：`"the way we learn"`
- 问题：`"What grammar structure is used here?"`
- 效果：选择完整短语进行语法分析

### 3. 句子理解
- 选择：`"The internet has revolutionized"`
- 问题：`"Can you explain this sentence?"`
- 效果：选择句子片段进行理解

## 下一步计划

1. **智能分词**：集成更高级的分词算法
2. **语义分组**：支持短语级别的智能分组
3. **多语言支持**：扩展支持其他语言的分词
4. **选择记忆**：记住用户的选择偏好
5. **批量操作**：支持批量选择相关词汇

这个基于token的选择功能为语言学习提供了更精确、更有效的文本选择体验！ 