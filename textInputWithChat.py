from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle

class TextInputWithChatApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history = []
        self.selected_text_backup = ""  # 备份选中的文本
        self.is_text_selected = False   # 标记是否有文本被选中
        self.selection_start = 0        # 选中文本的起始位置
        self.selection_end = 0          # 选中文本的结束位置
        self.original_text = """The Internet and Language Learning

The internet has revolutionized the way we learn languages. With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.

Online language learning platforms offer a variety of features that traditional classroom settings cannot provide. These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.

One of the most significant advantages of internet-based language learning is the availability of authentic materials. Learners can access real news articles, videos, podcasts, and social media content in their target language.

Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs. Students can connect with peers from different countries, practice conversation skills, and share cultural insights."""

    def build(self):
        # 主布局 - 改为垂直布局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 上方：文章阅读区域
        reading_panel = BoxLayout(orientation='vertical', size_hint_y=0.6, spacing=10)
        
        # 文章标题 - 白底黑字
        article_title = Label(
            text='Article: The Internet and Language Learning',
            size_hint_y=None,
            height=80,
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
            font_size=28
        )
        # 添加白色背景
        with article_title.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.article_title_bg = Rectangle(pos=article_title.pos, size=article_title.size)
        article_title.bind(pos=self._update_article_title_bg, size=self._update_article_title_bg)
        reading_panel.add_widget(article_title)
        
        # 文章内容 - 可选择的文本
        self.article_content = TextInput(
            text=self.original_text,
            readonly=True,
            multiline=True,
            size_hint_y=1,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 0),
            selection_color=(0.7, 0.9, 1, 0.5),
            font_size=28,
            padding=(10, 10),
            scroll_x=0,
            scroll_y=1,
            input_filter=self.block_input
        )
        reading_panel.add_widget(self.article_content)
        
        # 选中文本显示 - 白底黑字
        self.selection_label = Label(
            text='Selected Text: None',
            size_hint_y=None,
            height=120,
            color=(0.2, 0.2, 0.2, 1),
            text_size=(None, None),
            halign='left',
            valign='top',
            font_size=28
        )
        # 添加白色背景
        with self.selection_label.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.selection_label_bg = Rectangle(pos=self.selection_label.pos, size=self.selection_label.size)
        self.selection_label.bind(pos=self._update_selection_label_bg, size=self._update_selection_label_bg)
        reading_panel.add_widget(self.selection_label)
        
        # 下方：聊天区域
        chat_panel = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=10)
        
        # 聊天标题 - 白底黑字
        chat_title = Label(
            text='AI Assistant Chat',
            size_hint_y=None,
            height=80,
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
            font_size=28
        )
        # 添加白色背景
        with chat_title.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.chat_title_bg = Rectangle(pos=chat_title.pos, size=chat_title.size)
        chat_title.bind(pos=self._update_chat_title_bg, size=self._update_chat_title_bg)
        chat_panel.add_widget(chat_title)
        
        # 聊天历史滚动区域
        self.chat_scroll = ScrollView(size_hint_y=1)
        # 给ScrollView加白色背景
        with self.chat_scroll.canvas.before:
            Color(1, 1, 1, 1)
            self.chat_scroll_bg = Rectangle(pos=self.chat_scroll.pos, size=self.chat_scroll.size)
        self.chat_scroll.bind(pos=self._update_chat_scroll_bg, size=self._update_chat_scroll_bg)

        self.chat_container = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=20,
            padding=20
        )
        # 给GridLayout加白色背景
        with self.chat_container.canvas.before:
            Color(1, 1, 1, 1)
            self.chat_container_bg = Rectangle(pos=self.chat_container.pos, size=self.chat_container.size)
        self.chat_container.bind(pos=self._update_chat_container_bg, size=self._update_chat_container_bg)
        self.chat_container.bind(minimum_height=lambda instance, value: setattr(self.chat_container, 'height', value))
        self.chat_scroll.add_widget(self.chat_container)
        chat_panel.add_widget(self.chat_scroll)
        
        # 输入区域
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=160, spacing=10)
        
        # 文本输入框
        self.chat_input = TextInput(
            text='',
            multiline=False,
            size_hint_x=0.7,
            hint_text='Type your question here...',
            font_size=28,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1)
        )
        input_layout.add_widget(self.chat_input)
        
        # 发送按钮
        send_button = Button(
            text='Send',
            size_hint_x=0.3,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=28
        )
        send_button.bind(on_press=self.send_message)
        input_layout.add_widget(send_button)
        
        chat_panel.add_widget(input_layout)
        
        # 添加到主布局
        main_layout.add_widget(reading_panel)
        main_layout.add_widget(chat_panel)
        
        # 绑定回车键发送消息
        self.chat_input.bind(on_text_validate=self.send_message)
        
        # 绑定聊天输入框的焦点事件
        self.chat_input.bind(focus=self.on_chat_input_focus)
        
        # 绑定文章内容的选择变化事件
        self.article_content.bind(selection_text=self.on_text_selection_change)
        
        # 定期更新选中文本显示
        Clock.schedule_interval(self.update_selection_display, 0.1)
        
        # 添加欢迎消息
        self.add_chat_message("AI Assistant", "Hello! I'm here to help you with language learning. You can select any text from the article and ask me questions about it.", is_ai=True)
        
        return main_layout
    
    def block_input(self, text, from_undo):
        """阻止文章区域的输入"""
        return ''
    
    def on_chat_input_focus(self, instance, value):
        """处理聊天输入框焦点变化"""
        if value:  # 获得焦点时
            # 如果当前有选中的文本，备份它
            current_selection = self.get_selected_text()
            if current_selection:
                self.selected_text_backup = current_selection
                self.is_text_selected = True
                print(f"备份选中文本: {self.selected_text_backup}")
                # 保持文本高亮显示
                self.keep_text_highlighted()
        else:  # 失去焦点时
            # 检查是否点击了文章区域
            # 如果不是点击文章区域，则清除备份
            pass
    
    def on_text_selection_change(self, instance, value):
        """处理文本选择变化"""
        if value:  # 有选中文本
            self.selected_text_backup = value
            self.is_text_selected = True
            # 保存选择位置
            self.selection_start = self.article_content.selection_from
            self.selection_end = self.article_content.selection_to
            print(f"文本选择变化: {value} (位置: {self.selection_start}-{self.selection_end})")
        else:  # 没有选中文本
            # 只有在不是从聊天输入框切换回来时才清除
            if not self.chat_input.focus:
                self.selected_text_backup = ""
                self.is_text_selected = False
                self.selection_start = 0
                self.selection_end = 0
                print("清除选中文本备份")
            else:
                # 如果聊天输入框有焦点，保持高亮
                self.keep_text_highlighted()
    
    def update_selection_display(self, dt):
        """更新选中文本显示"""
        try:
            selected_text = self.get_selected_text()
            if selected_text:
                display_text = selected_text[:50] + "..." if len(selected_text) > 50 else selected_text
                # 如果有备份的选择，显示特殊标记
                if self.is_text_selected and self.selected_text_backup == selected_text:
                    self.selection_label.text = f'Selected Text (Backed up): "{display_text}"'
                else:
                    self.selection_label.text = f'Selected Text: "{display_text}"'
            else:
                self.selection_label.text = 'Selected Text: None'
        except Exception as e:
            self.selection_label.text = f'Selection Error: {e}'
    
    def get_selected_text(self):
        """获取选中的文本"""
        try:
            # 首先尝试从当前选择获取
            start, end = self.article_content.selection_from, self.article_content.selection_to
            if start != end:
                if start > end:
                    start, end = end, start
                selected_text = self.article_content.text[start:end]
                current_selection = selected_text.strip()
                if current_selection:
                    return current_selection
            
            # 如果当前没有选择，但有备份的选择，返回备份
            if self.is_text_selected and self.selected_text_backup:
                return self.selected_text_backup
            
            return ""
        except Exception as e:
            print(f"Error getting selected text: {e}")
            # 出错时也尝试返回备份
            if self.is_text_selected and self.selected_text_backup:
                return self.selected_text_backup
            return ""
    
    def keep_text_highlighted(self):
        """保持文本高亮显示"""
        if self.is_text_selected and self.selected_text_backup and self.selection_start != self.selection_end:
            try:
                # 使用select_text方法来设置选择
                self.article_content.select_text(self.selection_start, self.selection_end)
                print(f"保持高亮: {self.selection_start}-{self.selection_end}")
                
                # 强制更新显示
                Clock.schedule_once(self.force_selection_update, 0.1)
            except Exception as e:
                print(f"保持高亮时出错: {e}")
    
    def force_selection_update(self, dt):
        """强制更新选择显示"""
        try:
            # 重新设置选择范围
            if self.is_text_selected and self.selection_start != self.selection_end:
                self.article_content.select_text(self.selection_start, self.selection_end)
                print(f"强制更新选择: {self.selection_start}-{self.selection_end}")
        except Exception as e:
            print(f"强制更新选择时出错: {e}")
    
    def send_message(self, *args):
        """发送消息"""
        message = self.chat_input.text.strip()
        if not message:
            return
        
        # 获取选中的文本
        selected_text = self.get_selected_text()
        
        # 添加用户消息（包含引用格式）
        if selected_text:
            # 如果有选中的文本，显示引用格式
            self.add_chat_message("You", message, is_ai=False, quoted_text=selected_text)
        else:
            # 如果没有选中的文本，正常显示
            self.add_chat_message("You", message, is_ai=False)
        
        # 清空输入框
        self.chat_input.text = ''
        
        # 生成AI回复
        ai_response = self.generate_ai_response(message, selected_text)
        self.add_chat_message("AI Assistant", ai_response, is_ai=True)
    
    def add_chat_message(self, sender, message, is_ai=False, quoted_text=None):
        """添加聊天消息到界面"""
        # 创建消息容器（不再加canvas.before背景）
        message_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=160, padding=10)
        # 发送者标签 - 黑色文字
        sender_label = Label(
            text=sender,
            size_hint_y=None,
            height=40,
            color=(0.6, 0.6, 0.6, 1) if is_ai else (0.2, 0.6, 1, 1),
            halign='left',
            font_size=28
        )
        message_layout.add_widget(sender_label)
        # 如果有引用的文本，显示引用格式 - 黑色文字
        if quoted_text and not is_ai:
            quote_label = Label(
                text=f'Quote: "{quoted_text[:50]}{"..." if len(quoted_text) > 50 else ""}"',
                size_hint_y=None,
                height=60,
                color=(0.5, 0.5, 0.5, 1),
                text_size=(None, None),
                halign='left',
                valign='top',
                font_size=24
            )
            message_layout.add_widget(quote_label)
            message_label = Label(
                text=f'Says: {message}',
                size_hint_y=None,
                height=60,
                color=(0.2, 0.2, 0.2, 1),
                text_size=(None, None),
                halign='left',
                valign='top',
                font_size=28
            )
            message_layout.add_widget(message_label)
        else:
            message_label = Label(
                text=message,
                size_hint_y=None,
                height=120,
                color=(0.2, 0.2, 0.2, 1),
                text_size=(None, None),
                halign='left',
                valign='top',
                font_size=28
            )
            message_layout.add_widget(message_label)
        self.chat_container.add_widget(message_layout)
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, 'scroll_y', 0), 0.1)
    
    def _update_message_bg(self, *args):
        """更新消息背景"""
        if hasattr(self, 'message_bg'):
            self.message_bg.pos = args[0].pos
            self.message_bg.size = args[0].size
    
    def _update_article_title_bg(self, *args):
        """更新文章标题背景"""
        if hasattr(self, 'article_title_bg'):
            self.article_title_bg.pos = args[0].pos
            self.article_title_bg.size = args[0].size
    
    def _update_chat_title_bg(self, *args):
        """更新聊天标题背景"""
        if hasattr(self, 'chat_title_bg'):
            self.chat_title_bg.pos = args[0].pos
            self.chat_title_bg.size = args[0].size
    
    def _update_selection_label_bg(self, *args):
        """更新选中文本标签背景"""
        if hasattr(self, 'selection_label_bg'):
            self.selection_label_bg.pos = args[0].pos
            self.selection_label_bg.size = args[0].size
    
    def _update_chat_scroll_bg(self, *args):
        if hasattr(self, 'chat_scroll_bg'):
            self.chat_scroll_bg.pos = self.chat_scroll.pos
            self.chat_scroll_bg.size = self.chat_scroll.size
    def _update_chat_container_bg(self, *args):
        if hasattr(self, 'chat_container_bg'):
            self.chat_container_bg.pos = self.chat_container.pos
            self.chat_container_bg.size = self.chat_container.size
    
    def generate_ai_response(self, user_message, selected_text):
        """生成AI回复"""
        # 简单的AI回复逻辑
        if selected_text:
            if "meaning" in user_message.lower() or "意思" in user_message:
                return f"关于选中的文本 '{selected_text[:30]}...' 的意思，这是一个很好的问题。让我为您解释..."
            elif "grammar" in user_message.lower() or "语法" in user_message:
                return f"您选中的文本 '{selected_text[:30]}...' 涉及一些语法知识点。让我为您分析..."
            elif "pronunciation" in user_message.lower() or "发音" in user_message:
                return f"关于 '{selected_text[:30]}...' 的发音，这里有一些要点需要注意..."
            else:
                return f"您询问的是关于选中文本 '{selected_text[:30]}...' 的问题。这是一个很好的学习点！"
        else:
            if "help" in user_message.lower() or "帮助" in user_message:
                return "我可以帮助您学习语言！请选择文章中的任何文本，然后询问我关于语法、词汇、发音或意思的问题。"
            elif "hello" in user_message.lower() or "你好" in user_message:
                return "你好！我是您的语言学习助手。请选择文章中的文本，我会回答您的问题。"
            else:
                return "请先选择文章中的一些文本，然后询问我相关问题。我可以帮助您理解语法、词汇、发音等。"

if __name__ == '__main__':
    # 设置窗口大小
    Window.size = (1200, 800)
    app = TextInputWithChatApp()
    app.run() 