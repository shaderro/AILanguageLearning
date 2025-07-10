"""
卡片组件模块
包含各种可重用的卡片组件
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle


class BaseCard(ButtonBehavior, BoxLayout):
    """卡片基类，提供通用的边框和背景功能"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_border()
    
    def _setup_border(self):
        """设置卡片边框和背景"""
        with self.canvas.before:
            # 黑色边框
            Color(0, 0, 0, 1)
            self.border_rect = RoundedRectangle(radius=[15], pos=self.pos, size=self.size)
            # 白色背景
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[13], pos=(self.x+2, self.y+2), size=(self.width-4, self.height-4))
        
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        """更新边框和背景位置"""
        self.border_rect.pos = self.pos
        self.border_rect.size = self.size
        self.bg_rect.pos = (self.x+2, self.y+2)
        self.bg_rect.size = (self.width-4, self.height-4)


class ClickableCard(BaseCard):
    """可点击的文章卡片"""
    
    def __init__(self, title, words, level, percent, on_press_callback, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, 
                        size_hint_y=None, height=280, **kwargs)
        
        # 标题和等级
        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        top.add_widget(Label(
            text=f"[b][color=000000]{title}[/color][/b]", 
            markup=True, font_size=40, halign='left', valign='middle'
        ))
        top.add_widget(Label(
            text=f"[color=000000]{level}[/color]", 
            markup=True, font_size=32, size_hint_x=None, width=80, 
            halign='right', valign='middle'
        ))
        self.add_widget(top)
        
        # 单词数
        self.add_widget(Label(
            text=f"[color=000000]{words} words[/color]", 
            markup=True, font_size=30, size_hint_y=None, height=50, halign='left'
        ))
        
        # 进度条
        pb = ProgressBar(max=100, value=percent, height=30, size_hint_y=None)
        self.add_widget(pb)
        
        # 百分比和图标
        bottom = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        bottom.add_widget(Label(
            text=f"[color=000000]{percent}% read[/color]", 
            markup=True, font_size=30, halign='left'
        ))
        bottom.add_widget(Label(
            text="[color=000000]📖[/color]", 
            markup=True, font_size=36, size_hint_x=None, width=60, halign='right'
        ))
        self.add_widget(bottom)
        
        self.on_press_callback = on_press_callback
    
    def on_press(self):
        """点击事件处理"""
        if self.on_press_callback:
            self.on_press_callback()


class VocabCard(BaseCard):
    """词汇卡片"""
    
    def __init__(self, word, meaning, example, difficulty, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=8, 
                        size_hint_y=None, height=120, **kwargs)
        
        # 单词和难度
        top_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        top_row.add_widget(Label(
            text=f"[b][color=000000]{word}[/color][/b]", 
            markup=True, font_size=32, halign='left', valign='middle'
        ))
        
        # 根据难度设置颜色
        difficulty_color = self._get_difficulty_color(difficulty)
        top_row.add_widget(Label(
            text=f"[color=000000]{difficulty}[/color]", 
            markup=True, font_size=24, size_hint_x=None, width=60, 
            halign='right', valign='middle'
        ))
        self.add_widget(top_row)
        
        # 中文含义
        self.add_widget(Label(
            text=f"[color=000000]{meaning}[/color]", 
            markup=True, font_size=26, size_hint_y=None, height=30, halign='left'
        ))
        
        # 例句
        self.add_widget(Label(
            text=f"[color=666666]{example}[/color]", 
            markup=True, font_size=22, size_hint_y=None, height=25, halign='left'
        ))
    
    def _get_difficulty_color(self, difficulty):
        """根据难度返回颜色"""
        color_map = {
            "简单": (0.2, 0.8, 0.2, 1),
            "中等": (0.8, 0.6, 0.2, 1),
            "困难": (0.8, 0.2, 0.2, 1)
        }
        return color_map.get(difficulty, (0.5, 0.5, 0.5, 1)) 