"""
AI聊天模态窗口模块
以模态对话框形式显示，覆盖屏幕下半部分
"""

from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock

class AIChatModal(ModalView):
    """AI聊天模态窗口"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history = []
        self.current_article_title = ""
        self.current_article_content = ""
        self._setup_ui()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 设置模态窗口属性
        self.size_hint = (1, 0.6)  # 宽度100%，高度60%
        self.pos_hint = {'x': 0, 'y': 0}  # 从底部开始
        self.background_color = (0, 0, 0, 0.3)  # 半透明背景
        self.auto_dismiss = False  # 禁用自动关闭
        
        # 主容器
        main_layout = BoxLayout(orientation='vertical', spacing=5, padding=10)
        
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
            height=dp(40),
            padding=(5, 2)
        )
        
        # 关闭按钮
        close_btn = Button(
            text='✕',
            size_hint_x=None,
            width=dp(40),
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=dp(16)
        )
        close_btn.bind(on_press=self.dismiss)
        
        # 标题
        self.title_label = Label(
            text='AI Assistant',
            size_hint_x=1,
            halign='center',
            valign='middle',
            font_size=dp(16),
            bold=True
        )
        
        # 清空聊天按钮
        clear_btn = Button(
            text='Clear',
            size_hint_x=None,
            width=dp(60),
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1),
            font_size=dp(12)
        )
        clear_btn.bind(on_press=self.clear_chat)
        
        top_bar.add_widget(close_btn)
        top_bar.add_widget(self.title_label)
        top_bar.add_widget(clear_btn)
        
        parent_layout.add_widget(top_bar)
    
    def _setup_chat_area(self, parent_layout):
        """设置聊天历史区域"""
        # 聊天容器
        self.chat_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(5),
            padding=(5, 2)
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
            height=dp(50),
            spacing=dp(5),
            padding=(5, 2)
        )
        
        # 文本输入框
        self.input_field = TextInput(
            hint_text='输入您的问题...',
            multiline=False,
            size_hint_x=1,
            font_size=dp(14),
            padding=(8, 8)
        )
        self.input_field.bind(on_text_validate=self.send_message)
        
        # 发送按钮
        send_btn = Button(
            text='发送',
            size_hint_x=None,
            width=dp(60),
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=dp(14)
        )
        send_btn.bind(on_press=self.send_message)
        
        input_layout.add_widget(self.input_field)
        input_layout.add_widget(send_btn)
        
        parent_layout.add_widget(input_layout)
    
    def load_article_context(self, title, content):
        """加载文章上下文"""
        self.current_article_title = title
        self.current_article_content = content
        self.title_label.text = f'AI - {title[:20]}{"..." if len(title) > 20 else ""}'
        
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
            text_size=(Window.width * 0.8, None),
            color=(0.2, 0.2, 0.2, 1),
            padding=(5, 2),
            font_size=dp(14)
        )
        
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
            text_size=(Window.width * 0.8, None),
            color=(0.2, 0.2, 0.2, 1),
            padding=(5, 2),
            font_size=dp(14)
        )
        
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
        
        # 模拟AI回复
        self.simulate_ai_response(message)
    
    def simulate_ai_response(self, user_message):
        """模拟AI回复"""
        # 简单的关键词回复
        if "语法" in user_message or "grammar" in user_message.lower():
            response = "关于语法问题，我可以帮您分析文章中的语法结构。请具体说明您想了解哪个语法点。"
        elif "词汇" in user_message or "vocabulary" in user_message.lower():
            response = "我可以帮您解释文章中的词汇含义和用法。请告诉我您想了解哪个单词或短语。"
        elif "翻译" in user_message or "translate" in user_message.lower():
            response = "我可以帮您翻译文章内容。请指定您想翻译的具体句子或段落。"
        else:
            response = f"我理解您的问题：{user_message}。我正在分析文章《{self.current_article_title}》，请告诉我您具体想了解什么。"
        
        # 延迟显示AI回复，模拟思考时间
        Clock.schedule_once(lambda dt: self.add_ai_message(response), 0.5)
    
    def clear_chat(self, instance):
        """清空聊天记录"""
        self.chat_container.clear_widgets()
        self.chat_history = []
        
        # 重新添加欢迎消息
        if self.current_article_title:
            welcome_msg = f"您好！我是您的AI助手。我正在阅读文章《{self.current_article_title}》，有什么问题可以问我。"
            self.add_ai_message(welcome_msg)
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, 'scroll_y', 0), 0.1)
    
    def open(self, *args):
        """打开模态窗口时添加动画效果"""
        super().open(*args)
        # 添加从底部滑入的动画
        self.opacity = 0
        anim = Animation(opacity=1, duration=0.3)
        anim.start(self)


# 测试代码
if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.uix.boxlayout import BoxLayout
    
    class TestApp(App):
        def build(self):
            layout = BoxLayout(orientation='vertical')
            
            # 测试按钮
            test_btn = Button(text='打开AI聊天', size_hint_y=None, height=50)
            test_btn.bind(on_press=self.open_ai_chat)
            layout.add_widget(test_btn)
            
            # 添加一些测试内容
            for i in range(10):
                layout.add_widget(Button(text=f'测试内容 {i+1}'))
            
            return layout
        
        def open_ai_chat(self, instance):
            ai_modal = AIChatModal()
            ai_modal.load_article_context("测试文章标题", "这是测试文章内容")
            ai_modal.open()
    
    TestApp().run() 