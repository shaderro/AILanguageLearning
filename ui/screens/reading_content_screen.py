from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.modalview import ModalView
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
        
        # 为整个页面添加白色背景
        with main_layout.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.page_bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(pos=self._update_page_bg, size=self._update_page_bg)
        
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
            text='← Back',
            size_hint_x=None,
            width=100,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        back_btn.bind(on_press=self.go_back)
        
        # 标题
        self.title_label = Label(
            text='Article Title',
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
        content_scroll = ScrollView(size_hint=(1, 1))
        
        # 内容容器
        self.content_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,  # 不自动调整高度
            height=800,  # 设置固定高度
            spacing=15,
            padding=(0, 10, 0, 10)
        )
        
        # 文章内容标签 - 使用Label显示内容
        self.content_label = Label(
            text='Article content will be displayed here...',
            size_hint_y=1,  # 占据所有可用空间
            color=(0, 0, 0, 1),  # 黑色文字
            font_size=16,
            halign='left',
            valign='top',
            text_size=(None, None),  # 允许文本自动换行
            padding=(10, 10, 10, 10),  # 内边距
            markup=False,  # 禁用markup以避免格式问题
            text_language='en'  # 设置文本语言
        )
        
        # 绑定Label的尺寸变化，动态设置text_size
        self.content_label.bind(size=self._update_text_size)
        
        # 为文章内容添加白色背景
        with self.content_label.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.content_bg_rect = Rectangle(pos=self.content_label.pos, size=self.content_label.size)
        self.content_label.bind(pos=self._update_content_bg, size=self._update_content_bg)
        
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
            text='Learn',
            size_hint_x=0.5,
            background_color=(0.2, 0.8, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        learn_btn.bind(on_press=self.start_learning)
        
        # Ask AI按钮 - 固定在底部
        ask_ai_btn = Button(
            text='Ask AI (Relative)',
            size_hint_x=0.25,
            background_color=(0.8, 0.2, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        ask_ai_btn.bind(on_press=self.show_ai_chat_relative)
        
        # 测试ModalView版本的按钮
        test_modal_btn = Button(
            text='Test Modal',
            size_hint_x=0.25,
            background_color=(0.2, 0.8, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        test_modal_btn.bind(on_press=self.show_ai_chat_modal)
        
        # 引用选中文本按钮
        quote_selected_btn = Button(
            text='Quote',
            size_hint_x=0.25,
            background_color=(0.2, 0.8, 0.6, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        quote_selected_btn.bind(on_press=self.quote_selected_text)
        
        # 发送选中文本按钮
        send_selected_btn = Button(
            text='Send',
            size_hint_x=0.25,
            background_color=(0.8, 0.6, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        send_selected_btn.bind(on_press=self.send_current_selection)
        
        bottom_bar.add_widget(learn_btn)
        bottom_bar.add_widget(ask_ai_btn)
        bottom_bar.add_widget(quote_selected_btn)
        bottom_bar.add_widget(send_selected_btn)
        parent.add_widget(bottom_bar)
    
    def load_article(self, article_id, title, content):
        """加载文章内容"""
        self.article_id = article_id
        self.article_title = title
        self.article_content = content
        
        # 更新界面
        self.title_label.text = title
        self.content_label.text = content
        
        # 添加调试信息
        print(f"Loading article: {title}")
        print(f"Article content length: {len(content)}")
        print(f"Label content: {self.content_label.text[:100]}...")
    
    def go_back(self, instance):
        """返回上一页"""
        print(f"Going back to main page")
        # 返回到主屏幕
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'main'
        else:
            print("Cannot get screen manager")
    
    def start_learning(self, instance):
        """开始学习这篇文章"""
        print(f"Starting to learn article: {self.article_title}")
        # 这里可以跳转到学习页面或显示学习选项
    
    def favorite_article(self, instance):
        """收藏文章"""
        print(f"Favoriting article: {self.article_title}")
        # 这里可以添加收藏逻辑
    
    def show_ai_chat_relative(self, instance):
        """显示RelativeLayout版本的AI聊天窗口"""
        print("Showing RelativeLayout version of AI chat window")
        if not hasattr(self, 'ai_chat_relative'):
            self.ai_chat_relative = AIChatRelativeLayout()
            self.add_widget(self.ai_chat_relative)
            # 第一次创建时立即显示
            self.ai_chat_relative.show()
        else:
            # 如果已经存在但被移除了，重新添加
            if not self.ai_chat_relative.parent:
                self.add_widget(self.ai_chat_relative)
            self.ai_chat_relative.show()
    
    def show_ai_chat_modal(self, instance):
        """显示ModalView版本的AI聊天窗口 - 备用方法"""
        print("Showing ModalView version of AI chat window")
        if not hasattr(self, 'ai_chat_modal'):
            self.ai_chat_modal = AIChatModalView()
        self.ai_chat_modal.open()
    
    def on_enter(self):
        """屏幕进入时的回调"""
        print(f"Entering article reading page: {self.article_title}")
    
    def on_leave(self):
        """屏幕离开时的回调"""
        print("Leaving article reading page")
    
    def _update_content_bg(self, *args):
        """更新文章内容背景"""
        if hasattr(self, 'content_bg_rect'):
            self.content_bg_rect.pos = self.content_label.pos
            self.content_bg_rect.size = self.content_label.size

    def _update_text_size(self, instance, value):
        """更新Label的text_size，实现自动换行"""
        # 设置text_size为Label的实际尺寸（减去padding）
        padding_x = instance.padding[0] + instance.padding[2]  # 左右padding
        padding_y = instance.padding[1] + instance.padding[3]  # 上下padding
        instance.text_size = (instance.width - padding_x, None)

    
    def _update_page_bg(self, *args):
        """更新页面背景"""
        if hasattr(self, 'page_bg_rect'):
            self.page_bg_rect.pos = self.children[0].pos
            self.page_bg_rect.size = self.children[0].size
    

    
    def send_selected_text_to_chat(self, selected_text):
        """将选中的文本发送到聊天窗口"""
        if hasattr(self, 'ai_chat_relative') and self.ai_chat_relative.is_visible:
            # 如果聊天窗口已显示，直接添加选中的文本
            self.ai_chat_relative.add_selected_text(selected_text)
        else:
            # 如果聊天窗口未显示，先显示聊天窗口，然后添加文本
            self.show_ai_chat_relative(None)
            # 延迟一点时间确保聊天窗口已创建
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.ai_chat_relative.add_selected_text(selected_text), 0.1)

    def add_quote_to_chat_input(self, selected_text):
        """将选中的文本添加到聊天输入框"""
        if hasattr(self, 'ai_chat_relative') and self.ai_chat_relative.is_visible:
            # 如果聊天窗口已显示，直接添加到输入框
            self.ai_chat_relative.add_quote_to_input(selected_text)
        else:
            # 如果聊天窗口未显示，先显示聊天窗口，然后添加文本
            self.show_ai_chat_relative(None)
            # 延迟一点时间确保聊天窗口已创建
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.ai_chat_relative.add_quote_to_input(selected_text), 0.1)
    
    def quote_selected_text(self, instance):
        """引用选中的文本到聊天输入框"""
        print("Clicked quote selected button")
        # 由于Label不支持文本选择，暂时显示提示信息
        if hasattr(self, 'ai_chat_relative') and self.ai_chat_relative.is_visible:
            self.ai_chat_relative.add_message("Current using Label to display article content, text selection is not supported. Please use TextInput version for text selection.", is_user=False)
        else:
            # 如果聊天窗口未显示，先显示聊天窗口
            self.show_ai_chat_relative(None)
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.ai_chat_relative.add_message("Current using Label to display article content, text selection is not supported. Please use TextInput version for text selection.", is_user=False), 0.1)

    def send_current_selection(self, instance):
        """发送当前选中的文本到聊天"""
        print("Clicked send selected button")
        # 由于Label不支持文本选择，暂时显示提示信息
        if hasattr(self, 'ai_chat_relative') and self.ai_chat_relative.is_visible:
            self.ai_chat_relative.add_message("Current using Label to display article content, text selection is not supported. Please use TextInput version for text selection.", is_user=False)
        else:
            # 如果聊天窗口未显示，先显示聊天窗口
            self.show_ai_chat_relative(None)
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.ai_chat_relative.add_message("Current using Label to display article content, text selection is not supported. Please use TextInput version for text selection.", is_user=False), 0.1)


class AIChatRelativeLayout(RelativeLayout):
    """RelativeLayout版本的AI聊天窗口 - 覆盖屏幕下半部分"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_visible = False
        self.setup_ui()
        # 初始设置为隐藏状态，但不移除自身
        self.opacity = 0
        self.disabled = True
    
    def setup_ui(self):
        """设置聊天窗口界面"""
        # 设置位置和大小 - 覆盖屏幕下半部分，但留出底部按钮空间
        self.size_hint = (1, 0.4)  # 宽度100%，高度40%（减少高度避免覆盖按钮）
        self.pos_hint = {'x': 0, 'y': 0.1}  # 从底部10%开始，给按钮留空间
        
        # 设置背景色
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 0.95)  # 半透明白色背景
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 主容器
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
        
        # 1. 顶部栏 - 标题和关闭按钮
        self.setup_header(main_layout)
        
        # 2. 聊天消息区域
        self.setup_chat_area(main_layout)
        
        # 3. 输入区域
        self.setup_input_area(main_layout)
        
        self.add_widget(main_layout)
    
    def setup_header(self, parent):
        """设置顶部栏"""
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )
        
        # 标题
        title_label = Label(
            text='AI Assistant',
            size_hint_x=1,
            color=(0.2, 0.2, 0.2, 1),
            font_size=18,
            bold=True,
            halign='left'
        )
        
        # 关闭按钮
        close_btn = Button(
            text='×',
            size_hint_x=None,
            width=40,
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=20
        )
        close_btn.bind(on_press=self.hide)
        
        header.add_widget(title_label)
        header.add_widget(close_btn)
        parent.add_widget(header)
    
    def setup_chat_area(self, parent):
        """设置聊天消息区域"""
        # 聊天滚动视图
        self.chat_scroll = ScrollView(size_hint_y=1)
        
        # 聊天消息容器
        self.chat_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10,
            padding=(0, 5, 0, 5)
        )
        
        # 绑定高度
        self.chat_container.bind(
            minimum_height=lambda instance, value: setattr(self.chat_container, 'height', value)
        )
        
        # 添加欢迎消息
        welcome_msg = Label(
            text='Hello! I am an AI assistant. How can I help you?',
            size_hint_y=None,
            height=60,
            color=(0.3, 0.3, 0.3, 1),
            font_size=14,
            halign='left',
            valign='middle',
            text_size=(Window.width - 60, None),
            markup=True
        )
        self.chat_container.add_widget(welcome_msg)
        
        self.chat_scroll.add_widget(self.chat_container)
        parent.add_widget(self.chat_scroll)
    
    def setup_input_area(self, parent):
        """设置输入区域"""
        input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=10
        )
        
        # 文本输入框
        self.text_input = TextInput(
            text='',
            size_hint_x=1,
            multiline=False,
            font_size=14,
            hint_text='Enter your question...',
            background_color=(1, 1, 1, 1),
            foreground_color=(0.2, 0.2, 0.2, 1),
            cursor_color=(0.2, 0.6, 1, 1)
        )
        self.text_input.bind(on_text_validate=self.send_message)
        
        # 发送按钮
        send_btn = Button(
            text='Send',
            size_hint_x=None,
            width=80,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        send_btn.bind(on_press=self.send_message)
        
        input_layout.add_widget(self.text_input)
        input_layout.add_widget(send_btn)
        parent.add_widget(input_layout)
    
    def send_message(self, instance):
        """发送消息"""
        message = self.text_input.text.strip()
        if not message:
            return
        
        # 添加用户消息
        self.add_message(f"User: {message}", is_user=True)
        
        # 清空输入框
        self.text_input.text = ''
        
        # 模拟AI回复
        self.add_message("AI: I received your message and am processing it...", is_user=False)
    
    def add_message(self, text, is_user=False):
        """添加消息到聊天区域"""
        # 设置消息样式
        color = (0.2, 0.6, 1, 1) if is_user else (0.3, 0.3, 0.3, 1)
        align = 'right' if is_user else 'left'
        
        message_label = Label(
            text=text,
            size_hint_y=None,
            height=60,
            color=color,
            font_size=14,
            halign=align,
            valign='middle',
            text_size=(Window.width - 80, None),
            markup=True
        )
        
        self.chat_container.add_widget(message_label)
        
        # 滚动到底部
        self.chat_scroll.scroll_y = 0
    
    def add_selected_text(self, selected_text):
        """添加从文章中选择的文本到聊天"""
        # 添加用户选择的文本，使用引用格式
        quoted_text = f"> {selected_text}\n\nUser: Please help me analyze this text"
        self.add_message(quoted_text, is_user=True)
        
        # 模拟AI回复
        ai_response = f"I see you selected this text:\n\n> {selected_text}\n\nWhat would you like to know about this text? For example:\n• Grammar analysis\n• Vocabulary explanation\n• Translation\n• Writing tips"
        self.add_message(f"AI: {ai_response}", is_user=False)

    def add_quote_to_input(self, selected_text):
        """将选中的文本添加到聊天输入框"""
        # 格式化引用文本
        quote_text = f"> {selected_text}\n\n"
        
        # 如果输入框已有内容，在前面添加引用
        if self.text_input.text.strip():
            current_text = self.text_input.text
            self.text_input.text = quote_text + current_text
        else:
            # 如果输入框为空，直接设置引用文本
            self.text_input.text = quote_text
        
        # 将光标移动到文本末尾
        self.text_input.cursor = (len(self.text_input.text), 0)
        
        # 显示提示信息
        self.add_message("Selected text has been added to the input box. You can continue editing or send directly.", is_user=False)
    
    def show(self):
        """显示聊天窗口"""
        self.is_visible = True
        self.opacity = 1
        self.disabled = False
        print("AI chat window displayed")
    
    def hide(self, *args):
        """隐藏聊天窗口"""
        self.is_visible = False
        self.opacity = 0
        self.disabled = True
        # 隐藏时移除自身，避免拦截触摸事件
        if self.parent:
            self.parent.remove_widget(self)
        print("AI chat window hidden")
    
    def _update_bg(self, *args):
        """更新背景"""
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size


# 保留原有的ModalView版本作为备用
class AIChatModalView(ModalView):
    """ModalView版本的AI聊天窗口 - 备用版本"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.6)
        self.background_color = (0, 0, 0, 0.5)
        self.setup_ui()
    
    def setup_ui(self):
        """设置聊天窗口界面"""
        # 主容器
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
        
        # 1. 顶部栏
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )
        
        title_label = Label(
            text='AI Assistant (ModalView version)',
            size_hint_x=1,
            color=(0.2, 0.2, 0.2, 1),
            font_size=18,
            bold=True
        )
        
        close_btn = Button(
            text='×',
            size_hint_x=None,
            width=40,
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=20
        )
        close_btn.bind(on_press=self.dismiss)
        
        header.add_widget(title_label)
        header.add_widget(close_btn)
        main_layout.add_widget(header)
        
        # 2. 聊天区域
        chat_scroll = ScrollView(size_hint_y=1)
        chat_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10
        )
        chat_container.bind(
            minimum_height=lambda instance, value: setattr(chat_container, 'height', value)
        )
        
        welcome_msg = Label(
            text='Hello! I am an AI assistant. How can I help you?',
            size_hint_y=None,
            height=60,
            color=(0.3, 0.3, 0.3, 1),
            font_size=14
        )
        chat_container.add_widget(welcome_msg)
        
        chat_scroll.add_widget(chat_container)
        main_layout.add_widget(chat_scroll)
        
        # 3. 输入区域
        input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=10
        )
        
        text_input = TextInput(
            text='',
            size_hint_x=1,
            multiline=False,
            font_size=14,
            hint_text='Enter your question...'
        )
        
        send_btn = Button(
            text='Send',
            size_hint_x=None,
            width=80,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        
        input_layout.add_widget(text_input)
        input_layout.add_widget(send_btn)
        main_layout.add_widget(input_layout)
        
        self.add_widget(main_layout) 