"""
模态框组件模块
包含各种弹窗和模态框组件
"""

from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class AIChatModal(ModalView):
    """AI聊天模态框"""
    
    def __init__(self, sentence, **kwargs):
        super().__init__(
            size_hint=(0.8, 0.5), 
            auto_dismiss=False, 
            background_color=(1, 1, 1, 0.95), 
            **kwargs
        )
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # 标题
        layout.add_widget(Label(
            text='[b][color=000000]ask AI[/color][/b]', 
            markup=True, font_size=40, size_hint_y=None, height=80
        ))
        
        # 聊天内容
        chat_label = Label(
            text=f'[color=000000]你点击了：{sentence}\nAI: 你好，有什么问题可以问我！[/color]', 
            markup=True, font_size=28
        )
        layout.add_widget(chat_label)
        
        # 关闭按钮
        close_btn = Button(
            text='关闭', 
            font_size=28, 
            size_hint_y=None, 
            height=60, 
            background_normal='', 
            background_color=(0.2, 0.6, 1, 1), 
            color=(1, 1, 1, 1)
        )
        close_btn.bind(on_release=self.dismiss)
        layout.add_widget(close_btn)
        
        self.add_widget(layout) 