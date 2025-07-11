from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout

# 导入AI聊天模态窗口
try:
    from ai_chat_modal import AIChatModal
except ImportError:
    # 如果直接运行此文件，使用相对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from ai_chat_modal import AIChatModal

class ReadContentScreen(Screen):
    """简易文章内容屏幕"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.article_title = ""
        self.article_content = ""
        self._setup_ui()

    def _setup_ui(self):
        # 使用RelativeLayout作为主容器，这样可以固定按钮在底部
        main_layout = RelativeLayout()
        
        # 创建内容区域（除了底部按钮区域）
        content_layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        # 顶部返回按钮和标题
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        back_btn = Button(text='Back', size_hint_x=None, width=80)
        back_btn.bind(on_press=self.go_back)
        self.title_label = Label(text='标题', size_hint_x=1, halign='left', valign='middle')
        top_bar.add_widget(back_btn)
        top_bar.add_widget(self.title_label)
        content_layout.add_widget(top_bar)
        
        # 内容滚动区
        scroll = ScrollView(size_hint_y=1)
        self.content_label = Label(text='内容', size_hint_y=None, halign='left', valign='top')
        self.content_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll.add_widget(self.content_label)
        content_layout.add_widget(scroll)
        
        # 将内容区域添加到主布局，设置位置和大小（留出底部空间给按钮）
        main_layout.add_widget(content_layout)
        
        # 创建固定在底部的"Ask AI"按钮
        ask_ai_btn = Button(
            text='Ask AI',
            size_hint=(None, None),
            size=(120, 50),
            pos_hint={'center_x': 0.5, 'y': 0.02},  # 水平居中，距离底部2%
            background_color=(0.2, 0.6, 1, 1),  # 蓝色背景
            color=(1, 1, 1, 1)  # 白色文字
        )
        ask_ai_btn.bind(on_press=self.ask_ai)
        
        # 将按钮添加到主布局
        main_layout.add_widget(ask_ai_btn)
        
        self.add_widget(main_layout)

    def load_article(self, title, content):
        self.article_title = title
        self.article_content = content
        self.title_label.text = title
        self.content_label.text = content

    def go_back(self, instance):
        if self.manager:
            self.manager.current = 'main'
    
    def ask_ai(self, instance):
        """处理Ask AI按钮点击事件"""
        print(f"Ask AI按钮被点击，当前文章: {self.article_title}")
        
        # 创建并打开AI聊天模态窗口
        ai_modal = AIChatModal()
        ai_modal.load_article_context(self.article_title, self.article_content)
        ai_modal.open() 