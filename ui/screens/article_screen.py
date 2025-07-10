"""
文章屏幕模块
包含文章阅读界面
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle, Line
from functools import partial

# 修复导入路径 - 使用绝对导入
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.buttons import SubTabButton
from utils.swipe_handler import SwipeHandler


class ArticleScreen(Screen):
    """文章阅读屏幕"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.swipe_handler = SwipeHandler()
        
        self._setup_background()
        self._setup_layout()
        self._setup_back_button()
        self._setup_title()
        self._setup_content()
        self._setup_blank_content()
        self._setup_ai_chat()
    
    def _setup_background(self):
        """设置背景"""
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
    
    def _setup_layout(self):
        """设置主布局"""
        self.outer_box = BoxLayout(orientation='vertical')
        self.add_widget(self.outer_box)
    
    def _setup_back_button(self):
        """设置返回按钮"""
        back_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        back_btn = Button(
            text='back',
            size_hint=(None, None), size=(70, 36),
            background_normal='',
            background_color=(1, 1, 1, 1),
            color=(0, 0, 0, 1),
            border=(1, 1, 1, 1),
            font_size=32
        )
        
        with back_btn.canvas.before:
            Color(0, 0, 0, 1)
            self.back_line = Line(rectangle=(0, 0, 70, 36), width=1.2)
        
        def update_line(instance, value):
            self.back_line.rectangle = (instance.x, instance.y, instance.width, instance.height)
        
        back_btn.bind(pos=update_line, size=update_line)
        back_btn.bind(on_release=self.go_back)
        
        back_row.add_widget(back_btn)
        back_row.add_widget(Label())  # 占位符
        self.outer_box.add_widget(back_row)
    
    def _setup_title(self):
        """设置标题"""
        self.title_label = Label(
            text="", 
            markup=True, font_size=56, 
            size_hint_y=None, height=120
        )
        self.outer_box.add_widget(self.title_label)
    
    def _setup_content(self):
        """设置文章内容"""
        self.sentence_scroll = ScrollView(
            size_hint_y=1, 
            do_scroll_y=True, 
            do_scroll_x=False
        )
        self.sentence_vbox = BoxLayout(
            orientation='vertical', 
            size_hint_y=None, 
            spacing=8, 
            padding=(0, 0, 0, 0)
        )
        self.sentence_vbox.bind(
            minimum_height=lambda instance, value: setattr(self.sentence_vbox, 'height', value)
        )
        self.sentence_scroll.add_widget(self.sentence_vbox)
        self.outer_box.add_widget(self.sentence_scroll)
    
    def _setup_blank_content(self):
        """设置空白页内容"""
        blank_layout = BoxLayout(orientation='vertical')
        
        # 子标签栏
        sub_tab_row = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, height=50, 
            spacing=10, padding=(20, 0, 20, 0)
        )
        
        self.vocab_btn = SubTabButton('vocab', is_active=True)
        self.grammar_btn = SubTabButton('grammar', is_active=False)
        
        self.vocab_btn.bind(on_release=self.show_vocab)
        self.grammar_btn.bind(on_release=self.show_grammar)
        
        sub_tab_row.add_widget(self.vocab_btn)
        sub_tab_row.add_widget(self.grammar_btn)
        blank_layout.add_widget(sub_tab_row)
        
        # 内容区域
        content_container = RelativeLayout(size_hint_y=1)
        
        # Vocab内容
        vocab_scroll = ScrollView(
            size_hint=(1, 1), 
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        vocab_list = BoxLayout(
            orientation='vertical', 
            spacing=15, 
            size_hint_y=None, 
            padding=20
        )
        vocab_list.bind(
            minimum_height=lambda instance, value: setattr(vocab_list, 'height', value)
        )
        
        # 词汇数据
        vocab_data = [
            ("apple", "苹果", "I eat an apple every day.", "简单"),
            ("beautiful", "美丽的", "She is a beautiful girl.", "简单"),
            ("computer", "电脑", "I use my computer to work.", "简单"),
            ("determine", "决定", "You must determine your own path.", "中等"),
            ("efficient", "高效的", "This is an efficient method.", "中等"),
            ("fascinating", "迷人的", "The story is fascinating.", "困难"),
            ("generous", "慷慨的", "He is a generous person.", "中等"),
            ("happiness", "幸福", "Happiness comes from within.", "中等"),
            ("imagination", "想象力", "Children have vivid imagination.", "困难"),
            ("journey", "旅程", "Life is a journey.", "简单"),
            ("knowledge", "知识", "Knowledge is power.", "中等"),
            ("language", "语言", "English is a global language.", "简单"),
            ("magnificent", "壮丽的", "The view is magnificent.", "困难"),
            ("necessary", "必要的", "It is necessary to study hard.", "中等"),
            ("opportunity", "机会", "This is a great opportunity.", "困难"),
        ]
        
        from components.cards import VocabCard
        for word, meaning, example, difficulty in vocab_data:
            vocab_list.add_widget(VocabCard(word, meaning, example, difficulty))
        
        vocab_scroll.add_widget(vocab_list)
        
        self.vocab_content = vocab_scroll
        self.grammar_content = Label(
            text='[color=000000]这是grammar内容[/color]', 
            markup=True, font_size=36, halign='center', valign='middle', 
            size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.grammar_content.opacity = 0
        
        content_container.add_widget(self.vocab_content)
        content_container.add_widget(self.grammar_content)
        blank_layout.add_widget(content_container)
        
        # 绑定滑动手势
        self.swipe_handler.bind_to_widget(blank_layout, self._on_swipe)
        
        self.blank_content = blank_layout
        self.blank_content.opacity = 0
        self.blank_content.size_hint_y = 0
        self.blank_content.height = 0
        self.outer_box.add_widget(self.blank_content)
    
    def _setup_ai_chat(self):
        """设置AI聊天框"""
        self.ai_chat_box = BoxLayout(
            orientation='vertical', 
            size_hint_y=None, height=0, 
            opacity=0, padding=10, spacing=10
        )
        
        with self.ai_chat_box.canvas.before:
            Color(0, 0, 0, 1)
            self.ai_chat_border = Line(
                rectangle=(self.ai_chat_box.x, self.ai_chat_box.y, 
                          self.ai_chat_box.width, self.ai_chat_box.height), 
                width=2
            )
        
        def update_ai_chat_border(instance, value):
            self.ai_chat_border.rectangle = (
                self.ai_chat_box.x, self.ai_chat_box.y, 
                self.ai_chat_box.width, self.ai_chat_box.height
            )
        
        self.ai_chat_box.bind(pos=update_ai_chat_border, size=update_ai_chat_border)
        
        self.ai_chat_title = Label(
            text='[b][color=000000]ask AI[/color][/b]', 
            markup=True, font_size=40, size_hint_y=None, height=80
        )
        self.ai_chat_content = Label(text='', markup=True, font_size=28)
        
        # 聊天输入区
        input_row = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, height=60, spacing=10
        )
        self.input_field = TextInput(
            hint_text='输入消息...', 
            font_size=24, size_hint_x=0.8, 
            multiline=False, 
            background_color=(1, 1, 1, 1), 
            foreground_color=(0, 0, 0, 1), 
            cursor_color=(0, 0, 0, 1)
        )
        send_btn = Button(
            text='发送', 
            font_size=24, size_hint_x=0.2, 
            background_normal='', 
            background_color=(0.2, 0.6, 1, 1), 
            color=(1, 1, 1, 1)
        )
        send_btn.bind(on_release=self.send_ai_message)
        
        input_row.add_widget(self.input_field)
        input_row.add_widget(send_btn)
        
        self.ai_chat_box.add_widget(self.ai_chat_title)
        self.ai_chat_box.add_widget(self.ai_chat_content)
        self.ai_chat_box.add_widget(input_row)
        self.outer_box.add_widget(self.ai_chat_box)
    
    def _update_bg(self, *args):
        """更新背景"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def set_article(self, title, content):
        """设置文章内容"""
        self.title_label.text = f"[b][color=000000]{title}[/color][/b]"
        
        # 清空旧句子
        self.sentence_vbox.clear_widgets()
        
        # 测试内容
        content = (
            "This is a test article. This is the test content. Here is another sentence. "
            "And another one. Kivy is fun! Try clicking these sentences. Each one is a button. "
            "You can add as many as you like. The layout should scroll horizontally if needed. "
            "This is a very long sentence to test the horizontal scrolling behavior of the layout. "
            "Another test sentence. Yet another one. Keep going!"
        )
        
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        max_chars = 40
        line = []
        line_len = 0
        
        for s in sentences:
            btn = Button(
                text=s + '.',
                size_hint_x=None,
                background_normal='',
                background_color=(1, 1, 1, 1),
                color=(0, 0, 0, 1),
                font_size=32,
                padding=(12, 0),
                size_hint_y=None, height=80
            )
            btn.texture_update()
            btn.width = btn.texture_size[0] + 24
            btn.bind(on_release=partial(self.on_sentence_click, btn))
            line.append(btn)
            line_len += len(s)
            
            if line_len >= max_chars:
                hbox = BoxLayout(
                    orientation='horizontal', 
                    size_hint_y=None, height=80, spacing=4
                )
                for b in line:
                    hbox.add_widget(b)
                self.sentence_vbox.add_widget(hbox)
                line = []
                line_len = 0
        
        if line:
            hbox = BoxLayout(
                orientation='horizontal', 
                size_hint_y=None, height=80, spacing=4
            )
            for b in line:
                hbox.add_widget(b)
            self.sentence_vbox.add_widget(hbox)
        
        self.clicked_sentence = None
    
    def on_sentence_click(self, btn, *args):
        """句子点击事件"""
        # 遍历所有button，只有当前高亮
        for hbox in self.sentence_vbox.children:
            for b in hbox.children:
                if b is btn:
                    b.background_color = (0.2, 0.6, 1, 1)
                    b.color = (1, 1, 1, 1)
                else:
                    b.background_color = (1, 1, 1, 1)
                    b.color = (0, 0, 0, 1)
        
        # 显示AI chat box并更新内容
        self.ai_chat_content.text = f'[color=000000]你点击了：{btn.text}\nAI: 你好，有什么问题可以问我！[/color]'
        self.ai_chat_box.height = 300
        self.ai_chat_box.opacity = 1
    
    def go_back(self, *args):
        """返回主屏幕"""
        if self.manager:
            self.manager.current = 'main'
    
    def send_ai_message(self, *args):
        """发送AI消息"""
        msg = self.input_field.text.strip()
        if msg:
            old = self.ai_chat_content.text.rstrip()
            self.ai_chat_content.text = f"{old}\n你: {msg}\nAI: 这是AI的回复。"
            self.input_field.text = ''
    
    def show_vocab(self, *args):
        """显示词汇"""
        self.vocab_btn.set_active(True)
        self.grammar_btn.set_active(False)
        
        self.vocab_content.opacity = 1
        self.grammar_content.opacity = 0
    
    def show_grammar(self, *args):
        """显示语法"""
        self.vocab_btn.set_active(False)
        self.grammar_btn.set_active(True)
        
        self.vocab_content.opacity = 0
        self.grammar_content.opacity = 1
    
    def _on_swipe(self, direction):
        """处理滑动手势"""
        if direction == 'right':
            self.show_vocab()
        elif direction == 'left':
            self.show_grammar()


# 测试代码 - 如果直接运行此文件
if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    
    class TestApp(App):
        def build(self):
            sm = ScreenManager()
            article_screen = ArticleScreen(name="article")
            sm.add_widget(article_screen)
            return sm
    
    TestApp().run() 