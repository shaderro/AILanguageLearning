#!/usr/bin/env python3
"""
测试文本渲染修复效果
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.core.window import Window

class TextRenderingTestApp(App):
    """测试文本渲染的应用"""
    
    def build(self):
        """构建测试界面"""
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 测试标题
        title_label = Label(
            text="文本渲染测试 - Text Rendering Test",
            size_hint_y=None,
            height=50,
            color=(0, 0, 0, 1),
            font_size=24
        )
        main_layout.add_widget(title_label)
        
        # 创建滚动视图
        scroll_view = ScrollView(size_hint_y=1)
        
        # 内容容器
        content_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content_layout.bind(minimum_height=content_layout.setter('height'))
        
        # 测试文本1：英文
        test_text1 = """This is a test sentence with normal English text. 
The internet has revolutionized the way we learn languages. 
With the advent of online platforms, mobile applications, and digital resources, 
language learning has become more accessible than ever before."""
        
        label1 = Label(
            text=test_text1,
            size_hint_y=None,
            height=100,
            color=(0, 0, 0, 1),
            halign='left',
            valign='top',
            text_size=(Window.width - 40, None)
        )
        content_layout.add_widget(label1)
        
        # 测试文本2：德文（模拟图片中的问题文本）
        test_text2 = """Beider PChedewähwordesinBärbeBa©emei $ammitLarsKlingbeilzur Vorsitzende$owiTinklüsse dorfals$enera sekretäde
Mithreretwa31.
100nwohnelist dieStadtindeandesplanu as ittelzentrumilteilfunktionæin@oerzentradsgewiese"""
        
        label2 = Label(
            text=test_text2,
            size_hint_y=None,
            height=120,
            color=(0, 0, 0, 1),
            halign='left',
            valign='top',
            text_size=(Window.width - 40, None)
        )
        content_layout.add_widget(label2)
        
        # 测试文本3：中文
        test_text3 = """这是中文测试文本。
互联网彻底改变了我们学习语言的方式。
随着在线平台、移动应用程序和数字资源的出现，
语言学习变得比以往任何时候都更容易获得。"""
        
        label3 = Label(
            text=test_text3,
            size_hint_y=None,
            height=100,
            color=(0, 0, 0, 1),
            halign='left',
            valign='top',
            text_size=(Window.width - 40, None)
        )
        content_layout.add_widget(label3)
        
        # 测试文本4：混合语言
        test_text4 = """Mixed language test 混合语言测试:
English: The quick brown fox jumps over the lazy dog.
中文: 快速的棕色狐狸跳过懒狗。
Deutsch: Der schnelle braune Fuchs springt über den faulen Hund."""
        
        label4 = Label(
            text=test_text4,
            size_hint_y=None,
            height=120,
            color=(0, 0, 0, 1),
            halign='left',
            valign='top',
            text_size=(Window.width - 40, None)
        )
        content_layout.add_widget(label4)
        
        # 关闭按钮
        close_button = Button(
            text="关闭 / Close",
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.7, 1.0, 1)
        )
        close_button.bind(on_press=lambda x: App.get_running_app().stop())
        main_layout.add_widget(close_button)
        
        scroll_view.add_widget(content_layout)
        main_layout.add_widget(scroll_view)
        
        return main_layout

if __name__ == '__main__':
    print("🧪 启动文本渲染测试...")
    print("📝 测试内容：")
    print("   - 英文文本")
    print("   - 德文文本（模拟问题文本）")
    print("   - 中文文本")
    print("   - 混合语言文本")
    print("=" * 50)
    
    TextRenderingTestApp().run() 