"""
主屏幕模块
包含应用的主界面
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle
from functools import partial

# 导入组件 - 使用绝对导入
try:
    from components.cards import ClickableCard, VocabCard
    from components.buttons import TabButton, SubTabButton
    from utils.swipe_handler import SwipeHandler
except ImportError:
    # 如果直接运行此文件，使用相对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from components.cards import ClickableCard, VocabCard
    from components.buttons import TabButton, SubTabButton
    from utils.swipe_handler import SwipeHandler

class MainScreen(Screen):
    """主屏幕"""
    
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager
        self.swipe_handler = SwipeHandler()
        
        self._setup_background()
        self._setup_layout()
        #self._setup_topbar()
        self._setup_card_list()
        self._setup_blank_content()
        self._setup_tab_bar()
    
    def _setup_background(self):
        """设置背景"""
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
    
    def _setup_layout(self):
        """设置主布局"""
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)
    
    def _setup_topbar(self):
        """设置顶部栏"""
        topbar = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, padding=10)
        topbar.add_widget(Label(text="≡", font_size=60, size_hint_x=None, width=80))
        topbar.add_widget(Widget())
        self.layout.add_widget(topbar)
    
    def _setup_card_list(self):
        """设置卡片列表"""
        self.scroll = ScrollView()
        card_list = GridLayout(cols=1, spacing=30, size_hint_y=None, padding=20)
        card_list.bind(minimum_height=lambda instance, value: setattr(card_list, 'height', value))
        
        # 添加卡片数据
        data = [
            ("The Internet and Language", 450, "A2", 80),
            ("Modern Communication", 600, "B1", 50),
            ("Cultural Linguistics", 750, "B2", 30),
            ("Global Dialects", 500, "A2", 90),
        ]
        
        for title, words, level, percent in data:
            card_list.add_widget(ClickableCard(
                title, words, level, percent, 
                on_press_callback=partial(self.open_article, title)
            ))
        
        self.scroll.add_widget(card_list)
        self.layout.add_widget(self.scroll)
    
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
        vocab_scroll = ScrollView(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        vocab_list = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=20)
        vocab_list.bind(minimum_height=lambda instance, value: setattr(vocab_list, 'height', value))
        
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
        self.blank_content.size_hint_y = 1
        self.blank_content.height = 0
        self.layout.add_widget(self.blank_content)
    
    def _setup_tab_bar(self):
        """设置标签栏"""
        tab_row = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, height=60, 
            spacing=10, padding=(20, 0, 20, 0)
        )
        
        self.tab1_btn = TabButton('当前页面', is_active=True)
        self.tab2_btn = TabButton('空白页', is_active=False)
        
        self.tab1_btn.bind(on_release=self.show_tab1)
        self.tab2_btn.bind(on_release=self.show_tab2)
        
        tab_row.add_widget(self.tab1_btn)
        tab_row.add_widget(self.tab2_btn)
        self.layout.add_widget(tab_row)
    
    def _update_bg(self, *args):
        """更新背景"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def open_article(self, title):
        """打开文章"""
        article_title = title or "Test article name"
        article_content = "This is a test article. This is the test content...."
        
        if not self.screen_manager.has_screen("article"):
            try:
                from screens.article_screen import ArticleScreen
            except ImportError:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from screens.article_screen import ArticleScreen
            
            article_screen = ArticleScreen(name="article")
            self.screen_manager.add_widget(article_screen)
        else:
            article_screen = self.screen_manager.get_screen("article")
        
        article_screen.set_article(article_title, article_content)
        self.screen_manager.current = "article"
    
    def show_tab1(self, *args):
        """显示标签1"""
        self.tab1_btn.set_active(True)
        self.tab2_btn.set_active(False)
        
        self.scroll.opacity = 1
        self.blank_content.opacity = 0
        self.blank_content.size_hint_y = 0
        self.blank_content.height = 0
    
    def show_tab2(self, *args):
        """显示标签2"""
        self.tab1_btn.set_active(False)
        self.tab2_btn.set_active(True)
        
        self.scroll.opacity = 0
        self.blank_content.opacity = 1
        self.blank_content.size_hint_y = 1
    
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
            main_screen = MainScreen(sm, name="main")
            sm.add_widget(main_screen)
            return sm
    
    TestApp().run() 