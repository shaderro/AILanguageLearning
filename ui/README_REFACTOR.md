# UI 重构说明

## 📁 新的文件结构

```
ui/
├── components/           # 可重用组件
│   ├── __init__.py
│   ├── cards.py         # 卡片组件 (ClickableCard, VocabCard)
│   ├── buttons.py       # 按钮组件 (TabButton, SubTabButton)
│   └── modals.py        # 模态框组件 (AIChatModal)
├── screens/             # 屏幕界面
│   ├── __init__.py
│   ├── main_screen.py   # 主屏幕
│   └── article_screen.py # 文章屏幕
├── utils/               # 工具类
│   ├── __init__.py
│   └── swipe_handler.py # 滑动手势处理
├── app.py               # 主应用文件
├── main_refactored.py   # 重构后的主文件
└── main_test.py         # 原始文件 (保留)
```

## 🔧 重构优势

### 1. **模块化设计**
- **组件分离**: 每个UI组件都有独立的文件
- **职责清晰**: 每个模块只负责特定功能
- **易于维护**: 修改一个组件不会影响其他部分

### 2. **代码复用**
- **BaseCard**: 提供通用的卡片样式和边框
- **BorderedButton**: 可重用的带边框按钮
- **SwipeHandler**: 通用的滑动手势处理

### 3. **更好的组织结构**
- **components/**: 所有可重用UI组件
- **screens/**: 所有屏幕界面
- **utils/**: 工具类和辅助函数

## 📋 组件说明

### Cards (cards.py)
```python
# 基础卡片类
class BaseCard(ButtonBehavior, BoxLayout):
    # 提供通用的边框和背景功能

# 可点击的文章卡片
class ClickableCard(BaseCard):
    # 显示文章标题、等级、进度等信息

# 词汇卡片
class VocabCard(BaseCard):
    # 显示单词、含义、例句、难度
```

### Buttons (buttons.py)
```python
# 带边框的按钮基类
class BorderedButton(Button):
    # 自动处理边框绘制和更新

# 标签页按钮
class TabButton(BorderedButton):
    # 支持激活/非激活状态切换

# 子标签页按钮
class SubTabButton(TabButton):
    # 较小的标签页按钮
```

### Screens (screens/)
```python
# 主屏幕
class MainScreen(Screen):
    # 包含卡片列表、标签切换、滑动手势

# 文章屏幕
class ArticleScreen(Screen):
    # 包含文章内容、AI聊天、词汇/语法切换
```

## 🚀 使用方法

### 1. 运行重构后的应用
```bash
cd ui
python main_refactored.py
```

### 2. 创建新组件
```python
# 在 components/ 目录下创建新文件
from .cards import BaseCard

class MyCustomCard(BaseCard):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 添加自定义内容
```

### 3. 创建新屏幕
```python
# 在 screens/ 目录下创建新文件
from kivy.uix.screenmanager import Screen

class MyCustomScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置屏幕内容
```

## 🔄 迁移指南

### 从原始文件迁移到新结构

1. **导入组件**:
```python
# 旧方式
from main_test import ClickableCard, VocabCard

# 新方式
from components.cards import ClickableCard, VocabCard
```

2. **使用工具类**:
```python
# 旧方式: 在每个屏幕中重复实现滑动手势
def on_blank_touch_down(self, touch, *args):
    # 重复的代码...

# 新方式: 使用 SwipeHandler
from utils.swipe_handler import SwipeHandler
swipe_handler = SwipeHandler()
swipe_handler.bind_to_widget(widget, callback)
```

3. **创建按钮**:
```python
# 旧方式: 手动设置边框和样式
btn = Button(...)
with btn.canvas.before:
    # 重复的边框代码...

# 新方式: 使用预定义按钮
from components.buttons import TabButton
btn = TabButton('标签', is_active=True)
```

## 📝 最佳实践

### 1. **组件设计原则**
- 每个组件只负责一个功能
- 使用继承减少重复代码
- 提供清晰的接口和文档

### 2. **文件组织**
- 相关功能放在同一目录
- 使用有意义的文件名
- 保持目录结构清晰

### 3. **代码风格**
- 添加详细的文档字符串
- 使用类型提示（如果可能）
- 遵循PEP 8规范

## 🔧 扩展建议

### 1. **添加新功能**
- 在 `components/` 中添加新组件
- 在 `screens/` 中添加新屏幕
- 在 `utils/` 中添加新工具

### 2. **数据管理**
- 考虑添加 `models/` 目录管理数据
- 添加 `services/` 目录处理业务逻辑

### 3. **配置管理**
- 添加 `config/` 目录管理应用配置
- 使用配置文件管理样式和主题

## 🐛 注意事项

1. **导入路径**: 确保导入路径正确
2. **依赖关系**: 注意组件间的依赖关系
3. **性能**: 避免在组件初始化时进行复杂计算
4. **内存**: 及时清理不需要的引用

## 📚 进一步学习

- [Kivy官方文档](https://kivy.org/doc/stable/)
- [Python模块化设计](https://docs.python.org/3/tutorial/modules.html)
- [软件架构设计模式](https://en.wikipedia.org/wiki/Software_design_pattern) 