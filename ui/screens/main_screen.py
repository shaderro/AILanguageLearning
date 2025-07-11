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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.swipe_handler = SwipeHandler()
        
        # 初始化数据控制器
        try:
            from data_managers.data_controller import DataController
            self.data_controller = DataController()
        except ImportError:
            print("无法导入DataController，使用模拟数据")
            self.data_controller = None
        
        # 存储卡片引用
        self.article_cards = []
        self.vocab_cards = []
        
        self._setup_background()
        self._load_data()
        self._setup_layout()
        #self._setup_topbar()
        self._setup_reading_page()
        self._setup_learn_page()
        self._setup_tab_bar()
        
        # 初始显示阅读卡片
        self.show_tab1()
    
    def _setup_background(self):
        """设置背景"""
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
    
    def _load_data(self):
        """加载数据"""
        if self.data_controller:
            try:
                self.data_controller.load_all_data()
                print("数据加载成功")
            except Exception as e:
                print(f"数据加载失败: {e}")
    
    def _setup_layout(self):
        """设置主布局"""
        # 主容器：垂直布局包含内容区域和tab栏
        self.layout = BoxLayout(orientation='vertical')
        
        # 内容区域：使用单个容器，动态切换内容
        self.content_container = BoxLayout(orientation='vertical', size_hint_y=1)
        self.layout.add_widget(self.content_container)
        
        self.add_widget(self.layout)
    
    def _setup_topbar(self):
        """设置顶部栏"""
        topbar = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, padding=10)
        topbar.add_widget(Label(text="≡", font_size=60, size_hint_x=None, width=80))
        topbar.add_widget(Widget())
        self.layout.add_widget(topbar)
    
    def _setup_reading_page(self):
        """设置卡片列表"""
        # 从数据控制器获取原始文本标题
        try:
            text_titles = self.data_controller.list_texts_by_title()
        except Exception as e:
            print(f"获取文本标题时出错: {e}")
            text_titles = []
        
        # 如果没有数据，使用测试数据
        if not text_titles:
            text_titles = [
                "The Internet and Language",
                "Modern Communication", 
                "Cultural Linguistics",
                "Global Dialects"
            ]
            print("使用测试文章数据")
        
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
    
    def _setup_learn_page(self):
        """设置学习页面内容区域 - 包含子tab bar和内容区域"""
        # 创建学习页面的主容器 - 占据所有可用空间
        self.learn_content_container = BoxLayout(orientation='vertical', size_hint_y=1, spacing=10, padding=20)
        
        # 添加边框用于调试
        with self.learn_content_container.canvas.before:
            Color(1, 0, 0, 1)  # 红色边框
            self.learn_border = Rectangle(pos=self.learn_content_container.pos, size=self.learn_content_container.size)
        self.learn_content_container.bind(pos=self._update_learn_border, size=self._update_learn_border)
        
        # 1. 添加子tab bar - 固定在顶部，不参与滚动
        self._setup_learn_sub_tab_bar()
        
        # 2. 添加内容滚动区域 - 只有这部分会滚动
        self._setup_learn_content_area()
        
        # 移除高度绑定，因为现在使用size_hint_y=1
        # self.learn_content_container.bind(minimum_height=lambda instance, value: setattr(self.learn_content_container, 'height', value))

    def _setup_learn_sub_tab_bar(self):
        """设置学习页面的子tab bar - 固定在顶部"""
        # 子tab bar容器 - 固定高度，不参与滚动
        sub_tab_row = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, height=50, 
            spacing=10, padding=(10, 5, 10, 5)
        )
        
        # 添加蓝色边框用于调试子tab bar
        with sub_tab_row.canvas.before:
            Color(0, 0, 1, 1)  # 蓝色边框
            self.sub_tab_border = Rectangle(pos=sub_tab_row.pos, size=sub_tab_row.size)
        sub_tab_row.bind(pos=self._update_sub_tab_border, size=self._update_sub_tab_border)
        
        # 创建子tab按钮
        self.sub_tab1_btn = TabButton('Grammar语法', is_active=True)
        self.sub_tab2_btn = TabButton('Vocabulary词汇', is_active=False)
        self.sub_tab3_btn = TabButton('Practice练习', is_active=False)
        
        # 绑定事件
        self.sub_tab1_btn.bind(on_release=self.show_grammar_content)
        self.sub_tab2_btn.bind(on_release=self.show_vocab_content)
        self.sub_tab3_btn.bind(on_release=self.show_practice_content)
        
        # 添加到子tab bar
        sub_tab_row.add_widget(self.sub_tab1_btn)
        sub_tab_row.add_widget(self.sub_tab2_btn)
        sub_tab_row.add_widget(self.sub_tab3_btn)
        
        # 添加到学习内容容器 - 子tab bar固定在顶部
        self.learn_content_container.add_widget(sub_tab_row)

    def _setup_learn_content_area(self):
        """设置学习内容滚动区域 - 只有这部分会滚动"""
        # 创建滚动视图 - 占据剩余空间
        self.learn_scroll = ScrollView(size_hint_y=1)
        
        # 添加绿色边框用于调试滚动区域
        with self.learn_scroll.canvas.before:
            Color(0, 1, 0, 1)  # 绿色边框
            self.scroll_border = Rectangle(pos=self.learn_scroll.pos, size=self.learn_scroll.size)
        self.learn_scroll.bind(pos=self._update_scroll_border, size=self._update_scroll_border)
        
        # 创建内容容器 - 只有这个容器内的内容会滚动
        self.learn_sub_content_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15, padding=10)
        # 重要：绑定高度，让内容容器高度根据内容自动调整
        self.learn_sub_content_container.bind(minimum_height=lambda instance, value: setattr(self.learn_sub_content_container, 'height', value))
        
        # 将内容容器添加到滚动视图
        self.learn_scroll.add_widget(self.learn_sub_content_container)
        
        # 将滚动视图添加到学习内容容器 - 滚动区域在子tab bar下方
        self.learn_content_container.add_widget(self.learn_scroll)
        
        # 初始显示语法内容
        self.show_grammar_content()

    def show_grammar_content(self, *args):
        """显示语法内容"""
        print("切换到grammar子tab")
        self.sub_tab1_btn.set_active(True)
        self.sub_tab2_btn.set_active(False)
        self.sub_tab3_btn.set_active(False)
        
        # 清空内容容器
        self.learn_sub_content_container.clear_widgets()
        
        # 添加语法相关内容
        grammar_label = Label(
            text='[color=333333]Grammar Learning\n语法学习内容[/color]', 
            markup=True, 
            font_size=24, 
            halign='center',
            size_hint_y=None,
            height=100
        )
        self.learn_sub_content_container.add_widget(grammar_label)
        
        # 添加一些语法规则卡片示例
        grammar_rules = [
            "Present Simple Tense - 一般现在时",
            "Past Simple Tense - 一般过去时", 
            "Present Perfect Tense - 现在完成时",
            "Future Simple Tense - 一般将来时"
        ]
        
        for rule in grammar_rules:
            rule_card = ClickableCard(
                rule, 0, "Grammar Rule", 0,
                on_press_callback=lambda r=rule: print(f"点击了语法规则: {r}")
            )
            self.learn_sub_content_container.add_widget(rule_card)
        
        # 调试信息：打印容器高度
        print(f"内容容器高度: {self.learn_sub_content_container.height}")
        print(f"滚动视图高度: {self.learn_scroll.height}")
        print(f"学习容器高度: {self.learn_content_container.height}")

    def show_vocab_content(self, *args):
        """显示词汇内容"""
        print("切换到vocab子tab")
        self.sub_tab1_btn.set_active(False)
        self.sub_tab2_btn.set_active(True)
        self.sub_tab3_btn.set_active(False)
        
        # 清空内容容器
        self.learn_sub_content_container.clear_widgets()
        
        # 添加词汇相关内容
        vocab_label = Label(
            text='[color=333333]Vocabulary Learning\n词汇学习内容[/color]', 
            markup=True, 
            font_size=24, 
            halign='center',
            size_hint_y=None,
            height=100
        )
        self.learn_sub_content_container.add_widget(vocab_label)
        
        # 添加一些词汇卡片示例
        vocab_words = [
            ("Beautiful", "美丽的", "She is a beautiful girl.", "简单"),
            ("Intelligent", "聪明的", "He is an intelligent student.", "中等"),
            ("Courageous", "勇敢的", "The courageous firefighter saved the child.", "困难"),
            ("Generous", "慷慨的", "She is generous to everyone.", "中等")
        ]
        for word, meaning, example, difficulty in vocab_words:
            vocab_card = VocabCard(word, meaning, example, difficulty)
            vocab_card.bind(on_press=lambda instance, w=word, m=meaning, e=example, d=difficulty: self.open_vocab_detail(w, m, e, d))
            self.learn_sub_content_container.add_widget(vocab_card)

    def show_practice_content(self, *args):
        """显示练习内容"""
        print("切换到practice子tab")
        self.sub_tab1_btn.set_active(False)
        self.sub_tab2_btn.set_active(False)
        self.sub_tab3_btn.set_active(True)
        
        # 清空内容容器
        self.learn_sub_content_container.clear_widgets()
        
        # 添加练习相关内容
        practice_label = Label(
            text='[color=333333]Practice Exercises\n练习题目内容[/color]', 
            markup=True, 
            font_size=24, 
            halign='center',
            size_hint_y=None,
            height=100
        )
        self.learn_sub_content_container.add_widget(practice_label)
        
        # 添加一些练习题目示例
        practice_questions = [
            "Question 1: Choose the correct tense",
            "Question 2: Fill in the blank with proper vocabulary",
            "Question 3: Translate the sentence",
            "Question 4: Grammar correction"
        ]
        
        for i, question in enumerate(practice_questions, 1):
            question_card = ClickableCard(
                question, 0, f"Practice {i}", 0,
                on_press_callback=lambda q=question: print(f"点击了练习题目: {q}")
            )
            self.learn_sub_content_container.add_widget(question_card)
    
    def _setup_tab_bar(self):
        """设置标签栏"""
        tab_row = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, height=60, 
            spacing=10, padding=(20, 0, 20, 0)
        )
        
        self.tab1_btn = TabButton('Read文章', is_active=True)
        self.tab2_btn = TabButton('Learn词汇', is_active=False)
        
        self.tab1_btn.bind(on_release=self.show_tab1)
        self.tab2_btn.bind(on_release=self.show_tab2)
        
        tab_row.add_widget(self.tab1_btn)
        tab_row.add_widget(self.tab2_btn)
        self.layout.add_widget(tab_row)
    
    def _update_bg(self, *args):
        """更新背景"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def open_article(self, text_id):
        print(f"点击了文章: {text_id}")
        # 用模拟内容
        title = text_id
        content = f"""The Internet and Language Learning

The internet has revolutionized the way we learn languages. With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.

Online language learning platforms offer a variety of features that traditional classroom settings cannot provide. These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world. Students can now practice their language skills at any time and from anywhere, making learning more flexible and convenient.

One of the most significant advantages of internet-based language learning is the availability of authentic materials. Learners can access real news articles, videos, podcasts, and social media content in their target language. This exposure to authentic language use helps develop natural communication skills and cultural understanding.

Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs. Students can connect with peers from different countries, practice conversation skills, and share cultural insights. This global connectivity creates a rich learning environment that goes beyond traditional textbook exercises.

However, it's important to note that while the internet provides excellent resources for language learning, it should be used as a supplement to, rather than a replacement for, structured learning programs. The most effective approach combines online resources with traditional learning methods to create a comprehensive language learning experience.

In conclusion, the internet has transformed language learning by making it more accessible, interactive, and engaging. As technology continues to evolve, we can expect even more innovative tools and platforms to emerge, further enhancing the language learning experience for students worldwide."""
        if self.manager:
            read_screen = self.manager.get_screen("read")
            read_screen.load_article(text_id, title, content)
            self.manager.current = "read"
    
    def show_tab1(self, *args):
        """显示标签1 - 文章列表"""
        self.tab1_btn.set_active(True)
        self.tab2_btn.set_active(False)
        
        # 清空容器
        self.content_container.clear_widgets()
        
        # 创建文章列表的滚动视图
        article_scroll = ScrollView(size_hint_y=1)
        article_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=20, padding=20)
        article_container.bind(minimum_height=lambda instance, value: setattr(article_container, 'height', value))
        
        # 添加文章卡片 - 先移除卡片，再重新添加
        for card in self.article_cards:
            # 如果卡片已经有父容器，先移除
            if card.parent:
                card.parent.remove_widget(card)
            article_container.add_widget(card)
        
        article_scroll.add_widget(article_container)
        self.content_container.add_widget(article_scroll)
    
    def show_tab2(self, *args):
        """显示标签2 - 学习页面"""
        self.tab1_btn.set_active(False)
        self.tab2_btn.set_active(True)
        
        # 清空容器，直接添加学习内容容器（不使用主滚动视图）
        self.content_container.clear_widgets()
        self.content_container.add_widget(self.learn_content_container)
    
    def _update_learn_border(self, *args):
        """更新学习页面边框"""
        self.learn_border.pos = self.learn_content_container.pos
        self.learn_border.size = self.learn_content_container.size

    def _update_sub_tab_border(self, *args):
        """更新子tab bar边框"""
        if hasattr(self, 'sub_tab_border'):
            self.sub_tab_border.pos = self.sub_tab1_btn.parent.pos
            self.sub_tab_border.size = self.sub_tab1_btn.parent.size

    def _update_scroll_border(self, *args):
        """更新滚动区域边框"""
        if hasattr(self, 'scroll_border'):
            self.scroll_border.pos = self.learn_scroll.pos
            self.scroll_border.size = self.learn_scroll.size

    def open_vocab_detail(self, word, meaning, example, difficulty):
        """跳转到词汇详情页"""
        if self.manager:
            vocab_screen = self.manager.get_screen("vocab_detail")
            # 这里可以传递数据，后续可扩展
            # vocab_screen.set_vocab(word, meaning, example, difficulty)
            self.manager.current = "vocab_detail"


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