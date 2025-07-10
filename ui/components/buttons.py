"""
按钮组件模块
包含各种自定义按钮组件
"""

from kivy.uix.button import Button
from kivy.graphics import Color, Line


class BorderedButton(Button):
    """带边框的按钮"""
    
    def __init__(self, border_width=1, **kwargs):
        super().__init__(**kwargs)
        self.border_width = border_width
        self._setup_border()
    
    def _setup_border(self):
        """设置按钮边框"""
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self._border = Line(
                rectangle=(self.x, self.y, self.width, self.height), 
                width=self.border_width
            )
        
        self.bind(pos=self._update_border, size=self._update_border)
    
    def _update_border(self, instance, value):
        """更新边框位置"""
        if hasattr(self, '_border'):
            self._border.rectangle = (instance.x, instance.y, instance.width, instance.height)


class TabButton(BorderedButton):
    """标签页按钮"""
    
    def __init__(self, text, is_active=False, **kwargs):
        # 设置默认样式
        default_kwargs = {
            'background_normal': '',
            'background_color': (0.2, 0.6, 1, 1) if is_active else (0.8, 0.8, 0.8, 1),
            'color': (1, 1, 1, 1) if is_active else (0, 0, 0, 1),
            'font_size': 28,
            'size_hint_x': 0.5,
            'border_width': 2
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)
        self.is_active = is_active
    
    def set_active(self, active):
        """设置按钮激活状态"""
        self.is_active = active
        if active:
            self.background_color = (0.2, 0.6, 1, 1)
            self.color = (1, 1, 1, 1)
        else:
            self.background_color = (0.8, 0.8, 0.8, 1)
            self.color = (0, 0, 0, 1)


class SubTabButton(TabButton):
    """子标签页按钮"""
    
    def __init__(self, text, is_active=False, **kwargs):
        default_kwargs = {
            'font_size': 24,
            'border_width': 1
        }
        default_kwargs.update(kwargs)
        super().__init__(text, is_active, **default_kwargs) 