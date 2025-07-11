from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager, Screen
from functools import partial
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.uix.modalview import ModalView
from kivy.uix.relativelayout import RelativeLayout

class ClickableCard(ButtonBehavior, BoxLayout):
    def __init__(self, title, words, level, percent, on_press_callback, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, size_hint_y=None, height=280, **kwargs)
        with self.canvas.before:
            # 黑色边框
            Color(0, 0, 0, 1)
            self.border_rect = RoundedRectangle(radius=[15], pos=self.pos, size=self.size)
            # 白色背景
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[13], pos=(self.x+2, self.y+2), size=(self.width-4, self.height-4))
        self.bind(pos=self._update_rect, size=self._update_rect)
        # 标题和等级
        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        top.add_widget(Label(text=f"[b][color=000000]{title}[/color][/b]", markup=True, font_size=40, halign='left', valign='middle'))
        top.add_widget(Label(text=f"[color=000000]{level}[/color]", markup=True, font_size=32, size_hint_x=None, width=80, halign='right', valign='middle'))
        self.add_widget(top)
        # 单词数
        self.add_widget(Label(text=f"[color=000000]{words} words[/color]", markup=True, font_size=30, size_hint_y=None, height=50, halign='left'))
        # 进度条
        pb = ProgressBar(max=100, value=percent, height=30, size_hint_y=None)
        self.add_widget(pb)
        # 百分比和图标
        bottom = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        bottom.add_widget(Label(text=f"[color=000000]{percent}% read[/color]", markup=True, font_size=30, halign='left'))
        bottom.add_widget(Label(text="[color=000000]📖[/color]", markup=True, font_size=36, size_hint_x=None, width=60, halign='right'))
        self.add_widget(bottom)
        self.on_press_callback = on_press_callback
    def _update_rect(self, *args):
        self.border_rect.pos = self.pos
        self.border_rect.size = self.size
        self.bg_rect.pos = (self.x+2, self.y+2)
        self.bg_rect.size = (self.width-4, self.height-4)
    def on_press(self):
        self.on_press_callback()

class VocabCard(ButtonBehavior, BoxLayout):
    def __init__(self, word, meaning, example, difficulty, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=8, size_hint_y=None, height=120, **kwargs)
        with self.canvas.before:
            # 黑色边框
            Color(0, 0, 0, 1)
            self.border_rect = RoundedRectangle(radius=[10], pos=self.pos, size=self.size)
            # 白色背景
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[8], pos=(self.x+2, self.y+2), size=(self.width-4, self.height-4))
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # 单词和难度
        top_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        top_row.add_widget(Label(text=f"[b][color=000000]{word}[/color][/b]", markup=True, font_size=32, halign='left', valign='middle'))
        difficulty_color = (0.2, 0.8, 0.2, 1) if difficulty == "简单" else (0.8, 0.6, 0.2, 1) if difficulty == "中等" else (0.8, 0.2, 0.2, 1)
        top_row.add_widget(Label(text=f"[color=000000]{difficulty}[/color]", markup=True, font_size=24, size_hint_x=None, width=60, halign='right', valign='middle'))
        self.add_widget(top_row)
        
        # 中文含义
        self.add_widget(Label(text=f"[color=000000]{meaning}[/color]", markup=True, font_size=26, size_hint_y=None, height=30, halign='left'))
        
        # 例句
        self.add_widget(Label(text=f"[color=666666]{example}[/color]", markup=True, font_size=22, size_hint_y=None, height=25, halign='left'))
        
    def _update_rect(self, *args):
        self.border_rect.pos = self.pos
        self.border_rect.size = self.size
        self.bg_rect.pos = (self.x+2, self.y+2)
        self.bg_rect.size = (self.width-4, self.height-4)

class AIChatModal(ModalView):
    def __init__(self, sentence, **kwargs):
        super().__init__(size_hint=(0.8, 0.5), auto_dismiss=False, background_color=(1,1,1,0.95), **kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        # 标题
        layout.add_widget(Label(text='[b][color=000000]ask AI[/color][/b]', markup=True, font_size=40, size_hint_y=None, height=80))
        # 聊天内容
        chat_label = Label(text=f'[color=000000]你点击了：{sentence}\nAI: 你好，有什么问题可以问我！[/color]', markup=True, font_size=28)
        layout.add_widget(chat_label)
        # 关闭按钮
        close_btn = Button(text='关闭', font_size=28, size_hint_y=None, height=60, background_normal='', background_color=(0.2,0.6,1,1), color=(1,1,1,1))
        close_btn.bind(on_release=self.dismiss)
        layout.add_widget(close_btn)
        self.add_widget(layout)

class ArticleScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        # 根布局
        self.outer_box = BoxLayout(orientation='vertical')
        # 返回按钮行
        back_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        back_btn = Button(text='back',
                          size_hint=(None, None), size=(70, 36),
                          background_normal='',
                          background_color=(1,1,1,1),
                          color=(0,0,0,1),
                          border=(1,1,1,1),
                          font_size=32)
        with back_btn.canvas.before:
            Color(0,0,0,1)
            self.back_line = Line(rectangle=(0,0,70,36), width=1.2)
        def update_line(instance, value):
            self.back_line.rectangle = (instance.x, instance.y, instance.width, instance.height)
        back_btn.bind(pos=update_line, size=update_line)
        back_btn.bind(on_release=self.go_back)
        back_row.add_widget(back_btn)
        back_row.add_widget(Widget())
        self.outer_box.add_widget(back_row)
        # 标题
        self.title_label = Label(text="", markup=True, font_size=56, size_hint_y=None, height=120)
        self.outer_box.add_widget(self.title_label)
        # 文章内容ScrollView
        self.sentence_scroll = ScrollView(size_hint_y=1, do_scroll_y=True, do_scroll_x=False)
        self.sentence_vbox = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=(0,0,0,0))
        self.sentence_vbox.bind(minimum_height=lambda instance, value: setattr(self.sentence_vbox, 'height', value))
        self.sentence_scroll.add_widget(self.sentence_vbox)
        self.outer_box.add_widget(self.sentence_scroll)
        # 空白页内容（初始隐藏）
        blank_layout = BoxLayout(orientation='vertical')
        # 子tab栏
        sub_tab_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10, padding=(20, 0, 20, 0))
        self.vocab_btn = Button(text='vocab', font_size=24, background_normal='', background_color=(0.2,0.6,1,1), color=(1,1,1,1), size_hint_x=0.5)
        self.grammar_btn = Button(text='grammar', font_size=24, background_normal='', background_color=(0.8,0.8,0.8,1), color=(0,0,0,1), size_hint_x=0.5)
        # 给子tab按钮添加边框
        with self.vocab_btn.canvas.before:
            Color(0,0,0,1)
            self.vocab_border = Line(rectangle=(self.vocab_btn.x, self.vocab_btn.y, self.vocab_btn.width, self.vocab_btn.height), width=1)
        with self.grammar_btn.canvas.before:
            Color(0,0,0,1)
            self.grammar_border = Line(rectangle=(self.grammar_btn.x, self.grammar_btn.y, self.grammar_btn.width, self.grammar_btn.height), width=1)
        def update_vocab_border(instance, value):
            self.vocab_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
        def update_grammar_border(instance, value):
            self.grammar_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
        self.vocab_btn.bind(pos=update_vocab_border, size=update_vocab_border)
        self.grammar_btn.bind(pos=update_grammar_border, size=update_grammar_border)
        self.vocab_btn.bind(on_release=self.show_vocab)
        self.grammar_btn.bind(on_release=self.show_grammar)
        sub_tab_row.add_widget(self.vocab_btn)
        sub_tab_row.add_widget(self.grammar_btn)
        blank_layout.add_widget(sub_tab_row)
        # 子tab内容区域
        content_container = RelativeLayout(size_hint_y=1)
        
        # Vocab内容 - 可滚动的单词卡片列表
        vocab_scroll = ScrollView(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        vocab_list = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=20)
        vocab_list.bind(minimum_height=lambda instance, value: setattr(vocab_list, 'height', value))
        
        # 添加单词卡片数据
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
        
        for word, meaning, example, difficulty in vocab_data:
            vocab_list.add_widget(VocabCard(word, meaning, example, difficulty))
        
        vocab_scroll.add_widget(vocab_list)
        
        self.vocab_content = vocab_scroll
        self.grammar_content = Label(text='[color=000000]这是grammar内容[/color]', markup=True, font_size=36, halign='center', valign='middle', size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.grammar_content.opacity = 0
        content_container.add_widget(self.vocab_content)
        content_container.add_widget(self.grammar_content)
        blank_layout.add_widget(content_container)
        # 绑定滑动手势
        blank_layout.bind(on_touch_down=self.on_blank_touch_down)
        blank_layout.bind(on_touch_move=self.on_blank_touch_move)
        blank_layout.bind(on_touch_up=self.on_blank_touch_up)
        self.blank_content = blank_layout
        self.blank_content.opacity = 0
        self.blank_content.size_hint_y = 0
        self.blank_content.height = 0
        self.outer_box.add_widget(self.blank_content)
        # AI chat box（初始隐藏）
        self.ai_chat_box = BoxLayout(orientation='vertical', size_hint_y=None, height=0, opacity=0, padding=10, spacing=10)
        with self.ai_chat_box.canvas.before:
            Color(0,0,0,1)
            self.ai_chat_border = Line(rectangle=(self.ai_chat_box.x, self.ai_chat_box.y, self.ai_chat_box.width, self.ai_chat_box.height), width=2)
        def update_ai_chat_border(instance, value):
            self.ai_chat_border.rectangle = (self.ai_chat_box.x, self.ai_chat_box.y, self.ai_chat_box.width, self.ai_chat_box.height)
        self.ai_chat_box.bind(pos=update_ai_chat_border, size=update_ai_chat_border)
        self.ai_chat_title = Label(text='[b][color=000000]ask AI[/color][/b]', markup=True, font_size=40, size_hint_y=None, height=80)
        self.ai_chat_content = Label(text='', markup=True, font_size=28)
        # 聊天输入区
        input_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
        self.input_field = TextInput(hint_text='输入消息...', font_size=24, size_hint_x=0.8, multiline=False, background_color=(1,1,1,1), foreground_color=(0,0,0,1), cursor_color=(0,0,0,1))
        send_btn = Button(text='发送', font_size=24, size_hint_x=0.2, background_normal='', background_color=(0.2,0.6,1,1), color=(1,1,1,1))
        send_btn.bind(on_release=self.send_ai_message)
        input_row.add_widget(self.input_field)
        input_row.add_widget(send_btn)
        self.ai_chat_box.add_widget(self.ai_chat_title)
        self.ai_chat_box.add_widget(self.ai_chat_content)
        self.ai_chat_box.add_widget(input_row)
        self.outer_box.add_widget(self.ai_chat_box)
        self.add_widget(self.outer_box)
    def set_article(self, title, content):
        self.title_label.text = f"[b][color=000000]{title}[/color][/b]"
        # 清空旧句子
        self.sentence_vbox.clear_widgets()
        # 更多测试句子
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
            btn = Button(text=s+'.',
                         size_hint_x=None,
                         background_normal='',
                         background_color=(1,1,1,1),
                         color=(0,0,0,1),
                         font_size=32,
                         padding=(12, 0),
                         size_hint_y=None, height=80)
            btn.texture_update()
            btn.width = btn.texture_size[0] + 24
            btn.bind(on_release=partial(self.on_sentence_click, btn))
            line.append(btn)
            line_len += len(s)
            if line_len >= max_chars:
                hbox = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=4)
                for b in line:
                    hbox.add_widget(b)
                self.sentence_vbox.add_widget(hbox)
                line = []
                line_len = 0
        if line:
            hbox = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=4)
            for b in line:
                hbox.add_widget(b)
            self.sentence_vbox.add_widget(hbox)
        self.clicked_sentence = None
    def on_sentence_click(self, btn, *args):
        # 遍历所有button，只有当前高亮
        for hbox in self.sentence_vbox.children:
            for b in hbox.children:
                if b is btn:
                    b.background_color = (0.2,0.6,1,1)
                    b.color = (1,1,1,1)
                else:
                    b.background_color = (1,1,1,1)
                    b.color = (0,0,0,1)
        # 显示AI chat box并更新内容
        self.ai_chat_content.text = f'[color=000000]你点击了：{btn.text}\nAI: 你好，有什么问题可以问我！[/color]'
        self.ai_chat_box.height = 300
        self.ai_chat_box.opacity = 1
    def hide_ai_chat(self, *args):
        self.ai_chat_box.height = 0
        self.ai_chat_box.opacity = 0
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    def go_back(self, *args):
        if self.manager:
            self.manager.current = 'main'
    def send_ai_message(self, *args):
        msg = self.input_field.text.strip()
        if msg:
            old = self.ai_chat_content.text.rstrip()
            self.ai_chat_content.text = f"{old}\n你: {msg}\nAI: 这是AI的回复。"
            self.input_field.text = ''
    def show_vocab(self, *args):
        # 切换到vocab tab
        self.vocab_btn.background_color = (0.2,0.6,1,1)
        self.vocab_btn.color = (1,1,1,1)
        self.grammar_btn.background_color = (0.8,0.8,0.8,1)
        self.grammar_btn.color = (0,0,0,1)
        # 显示vocab内容，隐藏grammar内容
        self.vocab_content.opacity = 1
        self.grammar_content.opacity = 0
    def show_grammar(self, *args):
        # 切换到grammar tab
        self.vocab_btn.background_color = (0.8,0.8,0.8,1)
        self.vocab_btn.color = (0,0,0,1)
        self.grammar_btn.background_color = (0.2,0.6,1,1)
        self.grammar_btn.color = (1,1,1,1)
        # 隐藏vocab内容，显示grammar内容
        self.vocab_content.opacity = 0
        self.grammar_content.opacity = 1
    def on_blank_touch_down(self, touch, *args):
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y
        self.swipe_threshold = 30  # 降低滑动阈值，更容易触发
        self.swipe_detected = False  # 防止重复触发
    def on_blank_touch_move(self, touch, *args):
        if not hasattr(self, 'touch_start_x') or self.swipe_detected:
            return
        dx = touch.x - self.touch_start_x
        dy = touch.y - self.touch_start_y
        # 如果水平滑动距离大于垂直滑动距离且超过阈值
        if abs(dx) > abs(dy) and abs(dx) > self.swipe_threshold:
            self.swipe_detected = True  # 标记已检测到滑动
            if dx > 0:  # 向右滑动，切换到vocab
                self.show_vocab()
            else:  # 向左滑动，切换到grammar
                self.show_grammar()
    def on_blank_touch_up(self, touch, *args):
        # 重置滑动状态
        if hasattr(self, 'swipe_detected'):
            self.swipe_detected = False

class MainScreen(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        layout = BoxLayout(orientation='vertical')
        # 顶部栏
        topbar = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, padding=10)
        topbar.add_widget(Label(text="≡", font_size=60, size_hint_x=None, width=80))
        topbar.add_widget(Widget())
        layout.add_widget(topbar)
        # 滚动卡片区
        scroll = ScrollView()
        card_list = GridLayout(cols=1, spacing=30, size_hint_y=None, padding=20)
        card_list.bind(minimum_height=lambda instance, value: setattr(card_list, 'height', value))
        # 添加卡片
        data = [
            ("The Internet and Language", 450, "A2", 80),
            ("Modern Communication", 600, "B1", 50),
            ("Cultural Linguistics", 750, "B2", 30),
            ("Global Dialects", 500, "A2", 90),
        ]
        for title, words, level, percent in data:
            card_list.add_widget(ClickableCard(title, words, level, percent, on_press_callback=partial(self.open_article, title)))
        scroll.add_widget(card_list)
        layout.add_widget(scroll)
        # 空白页内容（初始隐藏）
        blank_layout = BoxLayout(orientation='vertical')
        # 子tab栏
        sub_tab_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10, padding=(20, 0, 20, 0))
        self.vocab_btn = Button(text='vocab', font_size=24, background_normal='', background_color=(0.2,0.6,1,1), color=(1,1,1,1), size_hint_x=0.5)
        self.grammar_btn = Button(text='grammar', font_size=24, background_normal='', background_color=(0.8,0.8,0.8,1), color=(0,0,0,1), size_hint_x=0.5)
        # 给子tab按钮添加边框
        with self.vocab_btn.canvas.before:
            Color(0,0,0,1)
            self.vocab_border = Line(rectangle=(self.vocab_btn.x, self.vocab_btn.y, self.vocab_btn.width, self.vocab_btn.height), width=1)
        with self.grammar_btn.canvas.before:
            Color(0,0,0,1)
            self.grammar_border = Line(rectangle=(self.grammar_btn.x, self.grammar_btn.y, self.grammar_btn.width, self.grammar_btn.height), width=1)
        def update_vocab_border(instance, value):
            self.vocab_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
        def update_grammar_border(instance, value):
            self.grammar_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
        self.vocab_btn.bind(pos=update_vocab_border, size=update_vocab_border)
        self.grammar_btn.bind(pos=update_grammar_border, size=update_grammar_border)
        self.vocab_btn.bind(on_release=self.show_vocab)
        self.grammar_btn.bind(on_release=self.show_grammar)
        sub_tab_row.add_widget(self.vocab_btn)
        sub_tab_row.add_widget(self.grammar_btn)
        blank_layout.add_widget(sub_tab_row)
        # 子tab内容区域
        content_container = BoxLayout(orientation='vertical', size_hint_y=1)

        # Vocab内容 - 可滚动的单词卡片列表
        vocab_scroll = ScrollView(size_hint_y=1)
        vocab_list = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=20)
        vocab_list.bind(minimum_height=lambda instance, value: setattr(vocab_list, 'height', value))

        # 添加单词卡片数据
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

        for word, meaning, example, difficulty in vocab_data:
            vocab_list.add_widget(VocabCard(word, meaning, example, difficulty))

        vocab_scroll.add_widget(vocab_list)

        self.vocab_content = vocab_scroll
        self.grammar_content = Label(text='[color=000000]这是grammar内容[/color]', markup=True, font_size=36, halign='center', valign='middle', size_hint=(1, 1))
        self.grammar_content.opacity = 0
        content_container.add_widget(self.vocab_content)
        content_container.add_widget(self.grammar_content)
        blank_layout.add_widget(content_container)
        # 绑定滑动手势
        blank_layout.bind(on_touch_down=self.on_blank_touch_down)
        blank_layout.bind(on_touch_move=self.on_blank_touch_move)
        blank_layout.bind(on_touch_up=self.on_blank_touch_up)
        self.blank_content = blank_layout
        self.blank_content.opacity = 0
        self.blank_content.size_hint_y = 1
        self.blank_content.height = 0
        layout.add_widget(self.blank_content)
        # Tab栏（放在最下方）
        tab_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10, padding=(20, 0, 20, 0))
        self.tab1_btn = Button(text='当前页面', font_size=28, background_normal='', background_color=(0.2,0.6,1,1), color=(1,1,1,1), size_hint_x=0.5)
        self.tab2_btn = Button(text='空白页', font_size=28, background_normal='', background_color=(0.8,0.8,0.8,1), color=(0,0,0,1), size_hint_x=0.5)
        # 给tab按钮添加边框
        with self.tab1_btn.canvas.before:
            Color(0,0,0,1)
            self.tab1_border = Line(rectangle=(self.tab1_btn.x, self.tab1_btn.y, self.tab1_btn.width, self.tab1_btn.height), width=2)
        with self.tab2_btn.canvas.before:
            Color(0,0,0,1)
            self.tab2_border = Line(rectangle=(self.tab2_btn.x, self.tab2_btn.y, self.tab2_btn.width, self.tab2_btn.height), width=2)
        def update_tab1_border(instance, value):
            self.tab1_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
        def update_tab2_border(instance, value):
            self.tab2_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
        self.tab1_btn.bind(pos=update_tab1_border, size=update_tab1_border)
        self.tab2_btn.bind(pos=update_tab2_border, size=update_tab2_border)
        self.tab1_btn.bind(on_release=self.show_tab1)
        self.tab2_btn.bind(on_release=self.show_tab2)
        tab_row.add_widget(self.tab1_btn)
        tab_row.add_widget(self.tab2_btn)
        layout.add_widget(tab_row)
        self.add_widget(layout)
        self.screen_manager = screen_manager
        # 保存引用以便tab切换
        self.scroll = scroll
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    def open_article(self, title):
        article_title = title or "Test article name"
        article_content = "This is a test article. This is the test content...."
        if not self.screen_manager.has_screen("article"):
            article_screen = ArticleScreen(name="article")
            self.screen_manager.add_widget(article_screen)
        else:
            article_screen = self.screen_manager.get_screen("article")
        article_screen.set_article(article_title, article_content)
        self.screen_manager.current = "article"
    def show_tab1(self, *args):
        # 切换到当前页面tab
        self.tab1_btn.background_color = (0.2,0.6,1,1)
        self.tab1_btn.color = (1,1,1,1)
        self.tab2_btn.background_color = (0.8,0.8,0.8,1)
        self.tab2_btn.color = (0,0,0,1)
        # 显示卡片列表，隐藏空白页
        self.scroll.opacity = 1
        self.blank_content.opacity = 0
        self.blank_content.size_hint_y = 0
        self.blank_content.height = 0
    def show_tab2(self, *args):
        # 切换到空白页tab
        self.tab1_btn.background_color = (0.8,0.8,0.8,1)
        self.tab1_btn.color = (0,0,0,1)
        self.tab2_btn.background_color = (0.2,0.6,1,1)
        self.tab2_btn.color = (1,1,1,1)
        # 隐藏卡片列表，显示空白页
        self.scroll.opacity = 0
        self.blank_content.opacity = 1
        self.blank_content.size_hint_y = 1
    def on_blank_touch_down(self, touch, *args):
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y
        self.swipe_threshold = 30  # 降低滑动阈值，更容易触发
        self.swipe_detected = False  # 防止重复触发
    def on_blank_touch_move(self, touch, *args):
        if not hasattr(self, 'touch_start_x') or self.swipe_detected:
            return
        dx = touch.x - self.touch_start_x
        dy = touch.y - self.touch_start_y
        # 如果水平滑动距离大于垂直滑动距离且超过阈值
        if abs(dx) > abs(dy) and abs(dx) > self.swipe_threshold:
            self.swipe_detected = True  # 标记已检测到滑动
            if dx > 0:  # 向右滑动，切换到vocab
                self.show_vocab()
            else:  # 向左滑动，切换到grammar
                self.show_grammar()
    def on_blank_touch_up(self, touch, *args):
        # 重置滑动状态
        if hasattr(self, 'swipe_detected'):
            self.swipe_detected = False
    def show_vocab(self, *args):
        # 切换到vocab tab
        self.vocab_btn.background_color = (0.2,0.6,1,1)
        self.vocab_btn.color = (1,1,1,1)
        self.grammar_btn.background_color = (0.8,0.8,0.8,1)
        self.grammar_btn.color = (0,0,0,1)
        # 显示vocab内容，隐藏grammar内容
        self.vocab_content.opacity = 1
        self.grammar_content.opacity = 0
    def show_grammar(self, *args):
        # 切换到grammar tab
        self.vocab_btn.background_color = (0.8,0.8,0.8,1)
        self.vocab_btn.color = (0,0,0,1)
        self.grammar_btn.background_color = (0.2,0.6,1,1)
        self.grammar_btn.color = (1,1,1,1)
        # 隐藏vocab内容，显示grammar内容
        self.vocab_content.opacity = 0
        self.grammar_content.opacity = 1

class LangUIApp(App):
    def build(self):
        sm = ScreenManager()
        main_screen = MainScreen(sm, name="main")
        sm.add_widget(main_screen)
        return sm

if __name__ == '__main__':
    LangUIApp().run() 