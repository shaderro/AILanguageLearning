"""
AI聊天子屏幕模块
用于处理用户与AI的对话交互
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.window import Window
from kivy.metrics import dp

class AIChatSubScreen(Screen):
    """AI聊天子屏幕"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history = []
        self.current_article_title = ""
        self.current_article_content = ""
        self._setup_ui()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # 顶部栏
        self._setup_top_bar(main_layout)
        
        # 聊天历史区域
        self._setup_chat_area(main_layout)
        
        # 底部输入区域
        self._setup_input_area(main_layout)
        
        self.add_widget(main_layout)
    
    def _setup_top_bar(self, parent_layout):
        """设置顶部栏"""
        top_bar = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=dp(50),
            padding=(10, 5)
        )
        
        # 返回按钮
        back_btn = Button(
            text='← Back',
            size_hint_x=None,
            width=dp(80),
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(on_press=self.go_back)
        
        # 标题
        self.title_label = Label(
            text='AI Assistant',
            size_hint_x=1,
            halign='center',
            valign='middle',
            font_size=dp(18),
            bold=True
        )
        
        # 清空聊天按钮
        clear_btn = Button(
            text='Clear',
            size_hint_x=None,
            width=dp(80),
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        clear_btn.bind(on_press=self.clear_chat)
        
        top_bar.add_widget(back_btn)
        top_bar.add_widget(self.title_label)
        top_bar.add_widget(clear_btn)
        
        parent_layout.add_widget(top_bar)
    
    def _setup_chat_area(self, parent_layout):
        """设置聊天历史区域"""
        # 聊天容器
        self.chat_container = BoxLayout(
            orientation='vertical',
            size_hint_y=1,
            spacing=dp(10),
            padding=(10, 5)
        )
        
        # 滚动视图
        self.chat_scroll = ScrollView(size_hint_y=1)
        self.chat_scroll.add_widget(self.chat_container)
        
        # 绑定高度变化
        self.chat_container.bind(
            minimum_height=lambda instance, value: setattr(instance, 'height', value)
        )
        
        parent_layout.add_widget(self.chat_scroll)
    
    def _setup_input_area(self, parent_layout):
        """设置输入区域"""
        input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10),
            padding=(10, 5)
        )
        
        # 文本输入框
        self.input_field = TextInput(
            hint_text='输入您的问题...',
            multiline=False,
            size_hint_x=1,
            font_size=dp(16),
            padding=(10, 10)
        )
        self.input_field.bind(on_text_validate=self.send_message)
        
        # 发送按钮
        send_btn = Button(
            text='发送',
            size_hint_x=None,
            width=dp(80),
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1)
        )
        send_btn.bind(on_press=self.send_message)
        
        input_layout.add_widget(self.input_field)
        input_layout.add_widget(send_btn)
        
        parent_layout.add_widget(input_layout)
    
    def load_article_context(self, title, content):
        """加载文章上下文"""
        self.current_article_title = title
        self.current_article_content = content
        self.title_label.text = f'AI Assistant - {title}'
        
        # 添加欢迎消息
        welcome_msg = f"您好！我是您的AI助手。我正在阅读文章《{title}》，有什么问题可以问我。"
        self.add_ai_message(welcome_msg)
    
    def add_user_message(self, message):
        """添加用户消息"""
        if not message.strip():
            return
            
        # 创建用户消息标签
        user_label = Label(
            text=f"您: {message}",
            size_hint_y=None,
            height=dp(40),
            halign='left',
            valign='middle',
            text_size=(Window.width - dp(40), None),
            color=(0.2, 0.2, 0.2, 1),
            padding=(10, 5)
        )
        
        # 设置背景色
        with user_label.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.9, 0.9, 1, 1)  # 浅蓝色背景
            user_label.bg_rect = Rectangle(pos=user_label.pos, size=user_label.size)
        
        user_label.bind(pos=self._update_user_bg, size=self._update_user_bg)
        
        self.chat_container.add_widget(user_label)
        self.chat_history.append({"role": "user", "content": message})
        
        # 滚动到底部
        self.scroll_to_bottom()
    
    def add_ai_message(self, message):
        """添加AI消息"""
        # 创建AI消息标签
        ai_label = Label(
            text=f"AI: {message}",
            size_hint_y=None,
            height=dp(40),
            halign='left',
            valign='middle',
            text_size=(Window.width - dp(40), None),
            color=(0.2, 0.2, 0.2, 1),
            padding=(10, 5)
        )
        
        # 设置背景色
        with ai_label.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(1, 0.9, 0.9, 1)  # 浅红色背景
            ai_label.bg_rect = Rectangle(pos=ai_label.pos, size=ai_label.size)
        
        ai_label.bind(pos=self._update_ai_bg, size=self._update_ai_bg)
        
        self.chat_container.add_widget(ai_label)
        self.chat_history.append({"role": "ai", "content": message})
        
        # 滚动到底部
        self.scroll_to_bottom()
    
    def send_message(self, instance):
        """发送消息"""
        message = self.input_field.text.strip()
        if not message:
            return
        
        # 添加用户消息
        self.add_user_message(message)
        
        # 清空输入框
        self.input_field.text = ""
        
        # 模拟AI回复（这里可以集成真实的AI服务）
        self.simulate_ai_response(message)
    
    def simulate_ai_response(self, user_message):
        """模拟AI回复"""
        # 这里可以集成真实的AI服务
        # 目前使用简单的模拟回复
        import time
        time.sleep(0.5)  # 模拟处理时间
        
        # 简单的关键词回复
        if "语法" in user_message or "grammar" in user_message.lower():
            response = "关于语法问题，我可以帮您分析文章中的语法结构。请具体说明您想了解哪个语法点。"
        elif "词汇" in user_message or "vocabulary" in user_message.lower():
            response = "我可以帮您解释文章中的词汇含义和用法。请告诉我您想了解哪个单词或短语。"
        elif "翻译" in user_message or "translate" in user_message.lower():
            response = "我可以帮您翻译文章内容。请指定您想翻译的具体句子或段落。"
        else:
            response = f"我理解您的问题：{user_message}。我正在分析文章《{self.current_article_title}》，请告诉我您具体想了解什么。"
        
        self.add_ai_message(response)
    
    def clear_chat(self, instance):
        """清空聊天记录"""
        self.chat_container.clear_widgets()
        self.chat_history = []
        
        # 重新添加欢迎消息
        if self.current_article_title:
            welcome_msg = f"您好！我是您的AI助手。我正在阅读文章《{self.current_article_title}》，有什么问题可以问我。"
            self.add_ai_message(welcome_msg)
    
    def go_back(self, instance):
        """返回上一页"""
        if self.manager:
            self.manager.current = 'read'
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        # 延迟滚动，确保内容已更新
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, 'scroll_y', 0), 0.1)
    
    def _update_user_bg(self, instance, value):
        """更新用户消息背景"""
        if hasattr(instance, 'bg_rect'):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
    
    def _update_ai_bg(self, instance, value):
        """更新AI消息背景"""
        if hasattr(instance, 'bg_rect'):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size


# 测试代码
if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    
    class TestApp(App):
        def build(self):
            sm = ScreenManager()
            chat_screen = AIChatSubScreen(name="ai_chat")
            chat_screen.load_article_context("测试文章", "这是测试内容")
            sm.add_widget(chat_screen)
            return sm
    
    TestApp().run() 