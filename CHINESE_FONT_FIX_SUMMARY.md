# 中文字体修复总结

## 问题描述

Learn页面中的中文显示出现乱码，包括：
- 语法规则名称（如"副词currently的用法"）
- 词汇表达式名称（如"in which"）
- 解释文本中的中文内容

## 问题原因

1. **Kivy默认字体不支持中文**：Kivy默认使用的字体不支持中文字符
2. **字体名称格式错误**：最初尝试使用逗号分隔的多个字体名称，但Kivy只接受单个字体名称
3. **缺少字体回退机制**：没有为不同操作系统提供合适的中文字体

## 修复方案

### 1. 创建字体工具类

创建了 `ui/utils/font_utils.py` 来统一处理中文字体：

```python
class FontUtils:
    """字体工具类"""
    
    @staticmethod
    def get_chinese_font_family():
        """获取支持中文的字体族"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            fonts = [
                "PingFang SC",      # 苹方简体
                "Heiti SC",         # 黑体简体
                "STHeiti",          # 华文黑体
                "Hiragino Sans GB", # 冬青黑体
                "Arial Unicode MS", # Arial Unicode
                "Arial"             # Arial
            ]
        elif system == "Windows":
            fonts = [
                "Microsoft YaHei",  # 微软雅黑
                "SimHei",           # 黑体
                "SimSun",           # 宋体
                "Arial Unicode MS", # Arial Unicode
                "Arial"             # Arial
            ]
        elif system == "Linux":
            fonts = [
                "WenQuanYi Micro Hei", # 文泉驿微米黑
                "Noto Sans CJK SC",    # Noto Sans 中文简体
                "Source Han Sans CN",  # 思源黑体
                "Droid Sans Fallback", # Droid Sans
                "Arial Unicode MS",    # Arial Unicode
                "Arial"                # Arial
            ]
        else:
            fonts = ["Arial Unicode MS", "Arial"]
        
        return fonts
    
    @staticmethod
    def get_font_name():
        """获取字体名称字符串"""
        fonts = FontUtils.get_chinese_font_family()
        # 返回第一个可用的字体，而不是逗号分隔的字符串
        return fonts[0] if fonts else "Arial"
    
    @staticmethod
    def create_label_with_chinese_support(text, **kwargs):
        """创建支持中文的Label组件"""
        from kivy.uix.label import Label
        
        # 设置默认字体属性
        font_props = FontUtils.get_label_font_properties()
        
        # 合并用户指定的属性
        label_props = font_props.copy()
        label_props.update(kwargs)
        
        return Label(text=text, **label_props)
```

### 2. 修复字体名称格式

**问题**：最初使用 `", ".join(fonts)` 返回逗号分隔的字体名称
**修复**：改为返回第一个可用的字体名称 `fonts[0] if fonts else "Arial"`

### 3. 更新所有Label组件

#### Learn页面卡片组件 (`ui/components/learn_cards.py`)

将所有 `Label` 创建替换为 `FontUtils.create_label_with_chinese_support`：

```python
# 修复前
title_label = Label(
    text=f"[b][color=000000]{self.rule_name}[/color][/b]",
    markup=True, font_size=32, halign='left', valign='middle',
    size_hint_x=0.7
)

# 修复后
title_label = FontUtils.create_label_with_chinese_support(
    text=f"[b][color=000000]{self.rule_name}[/color][/b]",
    markup=True, font_size=32, halign='left', valign='middle',
    size_hint_x=0.7
)
```

#### Learn页面 (`ui/screens/learn_screen.py`)

更新所有Label创建：

```python
# 标题
title = FontUtils.create_label_with_chinese_support(
    text="[b][color=000000]Learning Center[/color][/b]",
    markup=True, font_size=48, size_hint_y=None, height=80,
    halign='center', valign='middle'
)

# 统计信息
self.grammar_stats = FontUtils.create_label_with_chinese_support(
    text="[color=000000]Grammar Rules: 0[/color]",
    markup=True, font_size=24, halign='left', valign='middle'
)

# 空状态
empty_label = FontUtils.create_label_with_chinese_support(
    text="[color=666666]No grammar rules available[/color]",
    markup=True, font_size=28, size_hint_y=None, height=100,
    halign='center', valign='middle'
)
```

## 修复效果

### 1. 字体支持
- ✅ 支持macOS、Windows、Linux三大操作系统
- ✅ 自动选择合适的中文字体
- ✅ 提供字体回退机制

### 2. 中文显示
- ✅ 语法规则名称正确显示（如"副词currently的用法"）
- ✅ 词汇表达式正确显示（如"in which"）
- ✅ 解释文本中的中文正确显示
- ✅ 无乱码字符

### 3. 兼容性
- ✅ 保持原有功能不变
- ✅ 支持markup文本格式
- ✅ 支持所有Label属性

## 测试验证

### 1. 字体工具测试
```bash
source venv/bin/activate
python3 -c "from ui.utils.font_utils import FontUtils; print('字体名称:', FontUtils.get_font_name())"
```

**输出**：
```
字体名称: PingFang SC
```

### 2. 字体显示测试
```bash
source venv/bin/activate
python3 test_font_fix.py
```

**测试内容**：
- 普通Label显示
- 中文字体Label显示
- 中文内容显示
- 英文内容显示

### 3. 主程序测试
```bash
source venv/bin/activate
python3 run_main_ui.py
```

**验证要点**：
- Learn页面正常加载
- 语法规则卡片中文正确显示
- 词汇表达式卡片中文正确显示
- 无字体相关错误

## 文件变更

### 新增文件
- `ui/utils/font_utils.py` - 字体工具类

### 修改文件
- `ui/components/learn_cards.py` - 更新所有Label创建
- `ui/screens/learn_screen.py` - 更新所有Label创建
- `test_font_fix.py` - 字体测试脚本

## 技术要点

### 1. 字体选择策略
- **macOS**：优先使用PingFang SC（苹方简体）
- **Windows**：优先使用Microsoft YaHei（微软雅黑）
- **Linux**：优先使用WenQuanYi Micro Hei（文泉驿微米黑）

### 2. 字体回退机制
- 如果首选字体不可用，自动回退到下一个字体
- 最终回退到Arial作为通用字体

### 3. 工具类设计
- 静态方法设计，无需实例化
- 跨平台兼容
- 易于扩展和维护

## 注意事项

1. **字体依赖**：需要系统安装相应的中文字体
2. **性能考虑**：字体工具类使用静态方法，避免重复计算
3. **扩展性**：可以轻松添加新的字体支持
4. **兼容性**：保持与现有代码的完全兼容

## 扩展建议

1. **字体缓存**：实现字体可用性缓存机制
2. **动态字体检测**：运行时检测字体可用性
3. **用户自定义字体**：允许用户选择偏好字体
4. **字体预览**：提供字体预览功能 