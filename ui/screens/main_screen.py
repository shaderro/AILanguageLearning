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
    from data_managers.data_controller import DataController
except ImportError:
    # 如果直接运行此文件，使用相对导入
    import sys
    import os
    # 添加项目根目录到Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(project_root)
    from components.cards import ClickableCard, VocabCard
    from components.buttons import TabButton, SubTabButton
    from utils.swipe_handler import SwipeHandler
    from data_managers.data_controller import DataController

class MainScreen(Screen):
    """主屏幕"""
    
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager
        self.swipe_handler = SwipeHandler()
        
        # 初始化数据控制器
        self.data_controller = DataController(max_turns=10)
        self._load_data()
        
        # 初始化卡片列表
        self.article_cards = []
        self.vocab_cards = []
        
        self._setup_background()
        self._setup_layout()
        #self._setup_topbar()
        self._setup_card_list()
        self._setup_vocab_content()
        #self._setup_blank_content()
        self._setup_tab_bar()
        
        # 初始显示文章tab
        self.show_tab1()
    
    def _setup_background(self):
        """设置背景"""
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
    
    def _load_data(self):
        """加载数据"""
        try:
            # 获取数据文件路径
            import os
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
            grammar_path = os.path.join(data_dir, 'grammar_rules.json')
            vocab_path = os.path.join(data_dir, 'vocab_expressions.json')
            text_path = os.path.join(data_dir, 'original_texts.json')
            dialogue_record_path = os.path.join(data_dir, 'dialogue_record.json')
            dialogue_history_path = os.path.join(data_dir, 'dialogue_history.json')
            
            # 加载数据
            self.data_controller.load_data(
                grammar_path, vocab_path, text_path, 
                dialogue_record_path, dialogue_history_path
            )
        except Exception as e:
            print(f"加载数据时出错: {e}")
    
    def _setup_layout(self):
        """设置主布局"""
        # 主容器：垂直布局包含内容区域和tab栏
        self.layout = BoxLayout(orientation='vertical')
        
        # 内容容器：使用单个ScrollView，动态切换内容
        self.content_scroll = ScrollView(size_hint_y=1)
        self.content_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=20, padding=20)
        self.content_container.bind(minimum_height=lambda instance, value: setattr(self.content_container, 'height', value))
        self.content_scroll.add_widget(self.content_container)
        self.layout.add_widget(self.content_scroll)
        
        self.add_widget(self.layout)
    
    def _setup_topbar(self):
        """设置顶部栏"""
        topbar = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, padding=10)
        topbar.add_widget(Label(text="≡", font_size=60, size_hint_x=None, width=80))
        topbar.add_widget(Widget())
        self.layout.add_widget(topbar)
    
    def _setup_card_list(self):
        """设置卡片列表"""
        # 从数据控制器获取原始文本标题
        try:
            text_titles = self.data_controller.list_texts_by_title()
        except Exception as e:
            print(f"获取文本标题时出错: {e}")
            text_titles = []
        
        # 为每个标题创建卡片
        for title in text_titles:
            # 使用默认值，因为目前只需要标题
            card = ClickableCard(
                title, 0, "N/A", 0, 
                on_press_callback=partial(self.open_article, title)
            )
            self.article_cards.append(card)
            print(f"创建卡片: {title}")  # 调试信息
            # 不直接添加到容器，由tab切换方法添加
    
    def _setup_vocab_content(self):
        """设置词汇内容区域"""
        # 从数据控制器获取词汇数据
        try:
            vocab_data = self.data_controller.get_all_vocab_data()
            print(f"获取到词汇数据数量: {len(vocab_data)}")  # 调试信息
        except Exception as e:
            print(f"获取词汇数据时出错: {e}")
            # 使用测试数据作为备用
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
            print(f"使用备用词汇数据数量: {len(vocab_data)}")  # 调试信息
        
        # 创建词汇内容容器
        self.vocab_content_container = BoxLayout(orientation='vertical')
        
        # 顶部切换bar
        sub_tab_row = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, height=50, 
            spacing=10, padding=(20, 0, 20, 0)
        )
        
        self.vocab_sub_btn = SubTabButton('vocab', is_active=True)
        self.grammar_sub_btn = SubTabButton('grammar', is_active=False)
        
        self.vocab_sub_btn.bind(on_release=self.show_vocab_sub)
        self.grammar_sub_btn.bind(on_release=self.show_grammar_sub)
        
        sub_tab_row.add_widget(self.vocab_sub_btn)
        sub_tab_row.add_widget(self.grammar_sub_btn)
        self.vocab_content_container.add_widget(sub_tab_row)
        
        # 内容区域
        content_container = RelativeLayout(size_hint_y=1)
        
        # Vocab内容
        vocab_scroll = ScrollView(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        vocab_list = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=20)
        vocab_list.bind(minimum_height=lambda instance, value: setattr(vocab_list, 'height', value))
        
        # 存储词汇卡片引用
        self.vocab_cards = []
        for word, meaning, example, difficulty in vocab_data:
            vocab_card = VocabCard(word, meaning, example, difficulty)
            self.vocab_cards.append(vocab_card)
            vocab_list.add_widget(vocab_card)
            print(f"创建词汇卡片: {word}")  # 调试信息
        
        print(f"总共创建了 {len(self.vocab_cards)} 个词汇卡片")  # 调试信息
        
        vocab_scroll.add_widget(vocab_list)
        
        # 确保vocab_scroll可见
        vocab_scroll.opacity = 1
        
        # Grammar内容
        self.grammar_content = Label(
            text='[color=000000]这是grammar内容[/color]', 
            markup=True, font_size=36, halign='center', valign='middle', 
            size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.grammar_content.opacity = 0
        
        content_container.add_widget(vocab_scroll)
        content_container.add_widget(self.grammar_content)
        self.vocab_content_container.add_widget(content_container)
        
        # 不直接添加到容器，由tab切换方法添加
    
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
        
        self.tab1_btn = TabButton('文章', is_active=True)
        self.tab2_btn = TabButton('词汇', is_active=False)
        
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
        print(f"点击了文章: {title}")  # 调试信息
        article_title = title or "Test article name"
        # 用data_controller查找对应OriginalText
        original_text = None
        for text_id in range(1, 100):  # 假设id不超过100
            text = self.data_controller.get_text_by_id(text_id)
            if text and text.text_title == article_title:
                original_text = text
                break
        if original_text and original_text.text_by_sentence:
            # 拼接所有句子
            article_content = '\n'.join([s.sentence_body for s in original_text.text_by_sentence])
        else:
            article_content = "未找到对应内容。"
        
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
        """显示标签1 - 文章列表"""
        self.tab1_btn.set_active(True)
        self.tab2_btn.set_active(False)
        
        # 清空容器，只添加文章卡片
        self.content_container.clear_widgets()
        for card in self.article_cards:
            self.content_container.add_widget(card)
    
    def show_tab2(self, *args):
        """显示标签2 - 词汇列表"""
        self.tab1_btn.set_active(False)
        self.tab2_btn.set_active(True)
        
        # 清空容器，添加词汇内容容器
        self.content_container.clear_widgets()
        self.content_container.add_widget(self.vocab_content_container)
    
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
    
    def show_vocab_sub(self, *args):
        """显示词汇子tab"""
        self.vocab_sub_btn.set_active(True)
        self.grammar_sub_btn.set_active(False)
        
        # 显示词汇内容，隐藏语法内容
        for card in self.vocab_cards:
            card.opacity = 1
        self.grammar_content.opacity = 0
    
    def show_grammar_sub(self, *args):
        """显示语法子tab"""
        self.vocab_sub_btn.set_active(False)
        self.grammar_sub_btn.set_active(True)
        
        # 隐藏词汇内容，显示语法内容
        for card in self.vocab_cards:
            card.opacity = 0
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