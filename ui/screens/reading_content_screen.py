from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder

class ReadingContentScreen(Screen):
    """文章阅读内容屏幕"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.article_title = ""
        self.article_content = ""
        self.article_id = None
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主容器
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        # 1. 顶部导航栏
        self.setup_top_bar(main_layout)
        
        # 2. 文章内容区域
        self.setup_content_area(main_layout)
        
        # 3. 底部操作栏
        self.setup_bottom_bar(main_layout)
        
        self.add_widget(main_layout)
    
    def setup_top_bar(self, parent):
        """设置顶部导航栏"""
        top_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=15,
            padding=(0, 10, 0, 10)
        )
        
        # 返回按钮
        back_btn = Button(
            text='← 返回',
            size_hint_x=None,
            width=100,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        back_btn.bind(on_press=self.go_back)
        
        # 标题
        self.title_label = Label(
            text='文章标题',
            size_hint_x=1,
            color=(0.2, 0.2, 0.2, 1),
            font_size=18,
            bold=True,
            halign='left',
            valign='middle'
        )
        
        top_bar.add_widget(back_btn)
        top_bar.add_widget(self.title_label)
        parent.add_widget(top_bar)
    
    def setup_content_area(self, parent):
        """设置文章内容区域"""
        # 内容滚动视图
        content_scroll = ScrollView(size_hint_y=1)
        
        # 内容容器
        self.content_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=15,
            padding=(0, 10, 0, 10)
        )
        
        # 绑定高度
        self.content_container.bind(
            minimum_height=lambda instance, value: setattr(self.content_container, 'height', value)
        )
        
        # 文章内容标签
        self.content_label = Label(
            text='文章内容将在这里显示...',
            size_hint_y=None,
            color=(0.3, 0.3, 0.3, 1),
            font_size=16,
            halign='left',
            valign='top',
            text_size=(Window.width - 60, None),  # 考虑padding
            markup=True
        )
        
        self.content_container.add_widget(self.content_label)
        content_scroll.add_widget(self.content_container)
        parent.add_widget(content_scroll)
    
    def setup_bottom_bar(self, parent):
        """设置底部操作栏"""
        bottom_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=80,
            spacing=15,
            padding=(0, 10, 0, 10)
        )
        
        # 学习按钮
        learn_btn = Button(
            text='开始学习',
            size_hint_x=0.5,
            background_color=(0.2, 0.8, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        learn_btn.bind(on_press=self.start_learning)
        
        # 收藏按钮
        favorite_btn = Button(
            text='收藏文章',
            size_hint_x=0.5,
            background_color=(1, 0.6, 0, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        favorite_btn.bind(on_press=self.favorite_article)
        
        bottom_bar.add_widget(learn_btn)
        bottom_bar.add_widget(favorite_btn)
        parent.add_widget(bottom_bar)
    
    def load_article(self, article_id, title, content):
        """加载文章内容"""
        self.article_id = article_id
        self.article_title = title
        self.article_content = content
        
        # 更新界面
        self.title_label.text = title
        self.content_label.text = content
    
    def go_back(self, instance):
        """返回上一页"""
        print(f"返回主页面")
        # 返回到主屏幕
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'main'
        else:
            print("无法获取屏幕管理器")
    
    def start_learning(self, instance):
        """开始学习这篇文章"""
        print(f"开始学习文章: {self.article_title}")
        # 这里可以跳转到学习页面或显示学习选项
    
    def favorite_article(self, instance):
        """收藏文章"""
        print(f"收藏文章: {self.article_title}")
        # 这里可以添加收藏逻辑
    
    def on_enter(self):
        """屏幕进入时的回调"""
        print(f"进入文章阅读页面: {self.article_title}")
    
    def on_leave(self):
        """屏幕离开时的回调"""
        print("离开文章阅读页面") 