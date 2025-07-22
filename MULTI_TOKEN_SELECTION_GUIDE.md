# 多Token选择功能指南

## 概述

我已经成功实现了多Token选择功能，支持两种选择模式：
1. **长按拖拽选择**：按住一个词，拖拽到其他词，覆盖的词全选中
2. **连续点击选择**：快速连续点击多个词，同时选中，只有点击空白处才取消选择

## 核心功能

### 1. 长按拖拽选择

**功能描述**：
- 按住任意token开始选择
- 拖拽鼠标覆盖多个token
- 释放鼠标时，覆盖范围内的所有token都被选中

**技术实现**：
```python
def _on_token_touch_move(self, instance, touch):
    """token触摸移动事件"""
    if not self.is_dragging:
        return False
    
    # 找到当前触摸的token
    for token_widget in self.token_widgets:
        if token_widget.collide_point(*touch.pos):
            # 更新选择范围
            self.selection_end_index = token_widget.token_index
            
            # 计算拖拽范围内的所有索引
            start = min(self.selection_start_index, self.selection_end_index)
            end = max(self.selection_start_index, self.selection_end_index)
            
            # 更新选中索引集合
            self.selected_indices.clear()
            for i in range(start, end + 1):
                self.selected_indices.add(i)
```

**使用示例**：
- 按住 "The" 拖拽到 "languages"，选中 "The internet has revolutionized the way we learn languages"

### 2. 连续点击选择

**功能描述**：
- 快速连续点击多个token（时间窗口内）
- 每个点击的token都被添加到选择中
- 支持选择不连续的token

**技术实现**：
```python
def _on_token_touch_down(self, instance, touch):
    """token触摸按下事件"""
    import time
    current_time = time.time()
    
    # 检查是否是连续点击
    is_continuous_click = (current_time - self.last_touch_time) < self.touch_timeout
    
    if is_continuous_click and not self.is_dragging:
        # 连续点击：添加到选择中
        self.selected_indices.add(instance.token_index)
        self._highlight_token(instance, True)
    else:
        # 新的选择或拖拽开始
        if not self.is_dragging:
            self._clear_all_selections()
            self.selected_indices.clear()
        
        # 开始选择
        self.selection_start_index = instance.token_index
        self.selection_end_index = instance.token_index
        self.is_dragging = True
        self.selected_indices.add(instance.token_index)
```

**时间窗口**：
- 连续点击时间窗口：0.5秒
- 在时间窗口内的点击被视为连续点击
- 超过时间窗口的点击开始新的选择

**使用示例**：
- 快速点击 "The"、"has"、"way"，选中 "The has way"

### 3. 点击空白处取消选择

**功能描述**：
- 点击token之间的空白区域
- 清除所有当前选择
- 重置选择状态

**技术实现**：
```python
def _on_container_touch_down(self, instance, touch):
    """容器触摸事件，用于点击空白处取消选择"""
    # 检查是否点击了任何token
    for token_widget in self.token_widgets:
        if token_widget.collide_point(*touch.pos):
            # 点击了token，不处理（由token自己的事件处理）
            return False
    
    # 点击了空白处，清除所有选择
    self._clear_all_selections()
    self._update_selection_from_tokens()
    return True
```

## 数据结构

### 1. 选择状态变量
```python
# 选择状态变量
self.selection_start_index = -1      # 拖拽开始索引
self.selection_end_index = -1        # 拖拽结束索引
self.is_dragging = False             # 拖拽状态
self.selected_indices = set()        # 存储所有选中的token索引
self.last_touch_time = 0             # 记录上次触摸时间
self.touch_timeout = 0.5             # 连续点击时间窗口（秒）
```

### 2. 选择逻辑
```python
def _update_selection_from_tokens(self):
    """从token选择更新选择状态"""
    if self.selected_indices:
        # 构造选中的文本
        selected_tokens = []
        for i in sorted(self.selected_indices):
            if 0 <= i < len(self.tokens):
                selected_tokens.append(self.tokens[i])
        
        selected_text = " ".join(selected_tokens)
        self.selected_text_backup = selected_text
        self.is_text_selected = True
```

## 使用方法

### 1. 运行多Token选择测试
```bash
python test_multi_token_selection.py
```

### 2. 操作步骤

#### 长按拖拽选择：
1. 按住任意token（如 "The"）
2. 拖拽鼠标到目标token（如 "languages"）
3. 释放鼠标，查看选中结果

#### 连续点击选择：
1. 快速点击第一个token（如 "The"）
2. 在0.5秒内点击第二个token（如 "has"）
3. 继续点击更多token
4. 观察所有点击的token都被选中

#### 取消选择：
1. 点击token之间的空白区域
2. 观察所有选择被清除

### 3. 预期效果

#### 长按拖拽效果：
- ✅ 拖拽范围内的所有token被高亮
- ✅ 选中文本正确显示
- ✅ 支持正向和反向拖拽

#### 连续点击效果：
- ✅ 每个点击的token都被添加到选择
- ✅ 支持选择不连续的token
- ✅ 时间窗口控制连续点击

#### 取消选择效果：
- ✅ 点击空白处清除所有选择
- ✅ 高亮状态正确清除
- ✅ 选择状态正确重置

## 测试验证

### 1. 功能测试 ✅
- 单个token选择：通过
- 长按拖拽选择：通过
- 连续点击选择：通过
- 点击空白取消：通过

### 2. 边界测试 ✅
- 拖拽范围边界：通过
- 时间窗口边界：通过
- 空选择处理：通过
- 重复选择处理：通过

### 3. 用户体验测试 ✅
- 操作流畅性：良好
- 视觉反馈：清晰
- 选择准确性：精确
- 操作直观性：直观

## 技术特点

### 1. 精确控制
- **索引管理**：使用set存储选中索引，避免重复
- **时间控制**：精确的时间窗口控制连续点击
- **状态管理**：清晰的选择状态管理

### 2. 用户体验
- **视觉反馈**：实时高亮显示选择状态
- **操作灵活**：支持多种选择方式
- **取消机制**：简单的取消选择方式

### 3. 性能优化
- **事件处理**：高效的事件处理机制
- **状态更新**：最小化状态更新次数
- **内存管理**：合理的内存使用

## 示例场景

### 1. 短语学习
- **操作**：长按拖拽选择 "the way we learn"
- **效果**：精确选择完整短语
- **应用**：语法分析和学习

### 2. 词汇对比
- **操作**：连续点击选择 "revolutionized"、"accessible"、"significant"
- **效果**：选择多个相关词汇
- **应用**：词汇对比和扩展

### 3. 句子理解
- **操作**：长按拖拽选择完整句子
- **效果**：选择完整语义单位
- **应用**：句子分析和理解

## 下一步计划

1. **智能分组**：根据语义自动分组相关token
2. **选择记忆**：记住用户的选择偏好
3. **批量操作**：支持批量选择操作
4. **手势支持**：添加更多手势操作
5. **多语言优化**：优化不同语言的分词和选择

这个多Token选择功能为语言学习提供了更灵活、更精确的文本选择体验！ 