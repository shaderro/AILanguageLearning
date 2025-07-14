from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.app import App

class TextInputChatScreen(Screen):
    """文章阅读和AI聊天屏幕 - 基于TextInputWithChatApp"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history = []
        self.selected_text_backup = ""
        self.is_text_selected = False
        self.selection_start = 0
        self.selection_end = 0
        self.is_checking_highlight = False  # 是否正在检查高亮
        self.highlight_rectangle = None  # 用于显示高亮的矩形
        self.original_text = """The Internet and Language Learning

The internet has revolutionized the way we learn languages. With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.

Online language learning platforms offer a variety of features that traditional classroom settings cannot provide. These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.

One of the most significant advantages of internet-based language learning is the availability of authentic materials. Learners can access real news articles, videos, podcasts, and social media content in their target language.

Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs. Students can connect with peers from different countries, practice conversation skills, and share cultural insights."""
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 顶部导航栏
        self.setup_top_bar(main_layout)
        
        # 上方：文章阅读区域
        reading_panel = BoxLayout(orientation='vertical', size_hint_y=0.6, spacing=10)
        
        # 文章标题
        self.article_title = Label(
            text='Article: The Internet and Language Learning',
            size_hint_y=None,
            height=80,
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
            font_size=28
        )
        # 添加白色背景
        with self.article_title.canvas.before:
            Color(1, 1, 1, 1)
            self.article_title_bg = Rectangle(pos=self.article_title.pos, size=self.article_title.size)
        self.article_title.bind(pos=self._update_article_title_bg, size=self._update_article_title_bg)
        reading_panel.add_widget(self.article_title)
        
        # 文章内容
        self.article_content = TextInput(
            text=self.original_text,
            readonly=False,  # 改为False以允许选择保持
            multiline=True,
            size_hint_y=1,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 0),  # 隐藏光标
            selection_color=(0.7, 0.9, 1, 0.5),
            font_size=28,
            padding=(10, 10),
            scroll_x=0,
            scroll_y=1,
            input_filter=self.block_input,  # 通过input_filter阻止输入
            write_tab=False  # 禁用Tab键输入
        )
        reading_panel.add_widget(self.article_content)
        
        # 选中文本显示
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
            Color(1, 1, 1, 1)
            self.selection_label_bg = Rectangle(pos=self.selection_label.pos, size=self.selection_label.size)
        self.selection_label.bind(pos=self._update_selection_label_bg, size=self._update_selection_label_bg)
        reading_panel.add_widget(self.selection_label)
        
        # 下方：聊天区域
        chat_panel = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=10)
        
        # 聊天标题
        self.chat_title = Label(
            text='AI Assistant Chat',
            size_hint_y=None,
            height=80,
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
            font_size=28
        )
        # 添加白色背景
        with self.chat_title.canvas.before:
            Color(1, 1, 1, 1)
            self.chat_title_bg = Rectangle(pos=self.chat_title.pos, size=self.chat_title.size)
        self.chat_title.bind(pos=self._update_chat_title_bg, size=self._update_chat_title_bg)
        chat_panel.add_widget(self.chat_title)
        
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
        
        # 绑定事件
        self.chat_input.bind(on_text_validate=self.send_message)
        self.chat_input.bind(focus=self.on_chat_input_focus)
        self.article_content.bind(selection_text=self.on_text_selection_change)
        
        # 定期更新选中文本显示
        Clock.schedule_interval(self.update_selection_display, 0.1)
        
        # 添加欢迎消息
        self.add_chat_message("AI Assistant", "Hello! I'm here to help you with language learning. You can select any text from the article and ask me questions about it.", is_ai=True)
        
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
        title_label = Label(
            text='Text Input with AI Chat',
            size_hint_x=1,
            color=(0.2, 0.2, 0.2, 1),
            font_size=18,
            bold=True,
            halign='left',
            valign='middle'
        )
        
        top_bar.add_widget(back_btn)
        top_bar.add_widget(title_label)
        parent.add_widget(top_bar)
    
    def block_input(self, text, from_undo):
        """阻止文章区域的输入"""
        return ''
    
    def on_chat_input_focus(self, instance, value):
        """处理聊天输入框焦点变化"""
        if value:  # 获得焦点时
            # 如果当前有选中的文本，备份它并保持高亮
            current_selection = self.get_selected_text()
            if current_selection:
                self.selected_text_backup = current_selection
                self.is_text_selected = True
                self.selection_start = self.article_content.selection_from
                self.selection_end = self.article_content.selection_to
                print(f"备份选中文本: {self.selected_text_backup}")
                # 立即恢复高亮，然后定期检查
                self.restore_text_highlight()
                # 定期检查并恢复高亮
                if not self.is_checking_highlight:
                    self.is_checking_highlight = True
                    Clock.schedule_interval(self.check_and_restore_highlight, 0.05)  # 更频繁的检查
        else:  # 失去焦点时
            # 停止定期检查
            if self.is_checking_highlight:
                Clock.unschedule(self.check_and_restore_highlight)
                self.is_checking_highlight = False
    
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
        selected_text = self.get_selected_text()
        # 如果没有当前选中文本，但有备份的选中文本，显示备份的
        if not selected_text and self.selected_text_backup and self.is_text_selected:
            selected_text = self.selected_text_backup
        
        if selected_text:
            display_text = f'Selected Text: "{selected_text[:50]}{"..." if len(selected_text) > 50 else ""}"'
            self.selection_label.text = display_text
        else:
            self.selection_label.text = 'Selected Text: None'
    
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
    
    def check_and_restore_highlight(self, dt):
        """检查并恢复文本高亮显示"""
        if self.is_text_selected and self.selected_text_backup:
            # 检查当前是否有选择
            current_selection = self.get_selected_text()
            if not current_selection:
                # 如果没有选择，恢复高亮
                self.keep_text_highlighted()
    
    def restore_text_highlight(self, dt=None):
        """恢复文本高亮显示"""
        if self.is_text_selected and self.selected_text_backup:
            try:
                # 使用select_text方法恢复选择
                self.article_content.select_text(self.selection_start, self.selection_end)
                # 强制更新显示
                self.update_selection_display(0)
                print(f"恢复文本高亮: {self.selected_text_backup[:30]}...")
            except Exception as e:
                print(f"恢复文本高亮失败: {e}")
    
    def send_message(self, *args):
        """发送消息"""
        message = self.chat_input.text.strip()
        if message:
            # 添加用户消息
            self.add_chat_message("You", message, is_ai=False)
            
            # 获取选中的文本
            selected_text = self.get_selected_text()
            if not selected_text and self.selected_text_backup:
                selected_text = self.selected_text_backup
            
            # 生成AI响应
            ai_response = self.generate_ai_response(message, selected_text)
            self.add_chat_message("AI Assistant", ai_response, is_ai=True, quoted_text=selected_text)
            
            # 清空输入框
            self.chat_input.text = ''
    
    def add_chat_message(self, sender, message, is_ai=False, quoted_text=None):
        """添加聊天消息"""
        # 创建消息容器
        message_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        message_layout.bind(minimum_height=lambda instance, value: setattr(message_layout, 'height', value))
        
        # 发送者标签
        sender_label = Label(
            text=sender,
            size_hint_y=None,
            height=30,
            color=(0.2, 0.6, 1, 1) if is_ai else (0.8, 0.2, 0.2, 1),
            font_size=20,
            bold=True,
            halign='left'
        )
        message_layout.add_widget(sender_label)
        
        # 如果有引用的文本，显示它
        if quoted_text:
            quoted_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
            quoted_layout.bind(minimum_height=lambda instance, value: setattr(quoted_layout, 'height', value))
            
            quoted_title = Label(
                text='Quoted Text:',
                size_hint_y=None,
                height=25,
                color=(0.4, 0.4, 0.4, 1),
                font_size=16,
                halign='left'
            )
            quoted_layout.add_widget(quoted_title)
            
            quoted_content = Label(
                text=f'"{quoted_text[:100]}{"..." if len(quoted_text) > 100 else ""}"',
                size_hint_y=None,
                height=40,
                color=(0.6, 0.6, 0.6, 1),
                font_size=14,
                halign='left',
                text_size=(self.chat_scroll.width - 40, None)
            )
            quoted_content.bind(
                texture_size=lambda instance, value: setattr(quoted_content, 'height', value[1])
            )
            quoted_layout.add_widget(quoted_content)
            
            message_layout.add_widget(quoted_layout)
        
        # 消息内容
        message_label = Label(
            text=message,
            size_hint_y=None,
            color=(0.2, 0.2, 0.2, 1),
            font_size=18,
            halign='left',
            valign='top',
            text_size=(self.chat_scroll.width - 40, None)
        )
        message_label.bind(
            texture_size=lambda instance, value: setattr(message_label, 'height', value[1])
        )
        message_layout.add_widget(message_label)
        
        # 添加到聊天容器
        self.chat_container.add_widget(message_layout)
        
        # 滚动到底部
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, 'scroll_y', 0), 0.1)
    
    def generate_ai_response(self, user_message, selected_text):
        """生成AI响应"""
        if selected_text:
            return f"I see you've selected: '{selected_text[:50]}{'...' if len(selected_text) > 50 else ''}'. Regarding your question '{user_message}', here's my response: This is a simulated AI response. In a real implementation, this would connect to an AI service to provide helpful language learning assistance."
        else:
            return f"Thank you for your question: '{user_message}'. This is a simulated AI response. In a real implementation, this would connect to an AI service to provide helpful language learning assistance."
    
    def go_back(self, instance):
        """返回上一页"""
        print("Going back to main page")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'main'
    
    def _update_article_title_bg(self, *args):
        """更新文章标题背景"""
        if hasattr(self, 'article_title_bg'):
            self.article_title_bg.pos = self.article_title.pos
            self.article_title_bg.size = self.article_title.size
    
    def _update_chat_title_bg(self, *args):
        """更新聊天标题背景"""
        if hasattr(self, 'chat_title_bg') and hasattr(self, 'chat_title'):
            self.chat_title_bg.pos = self.chat_title.pos
            self.chat_title_bg.size = self.chat_title.size
    
    def _update_selection_label_bg(self, *args):
        """更新选中文本标签背景"""
        if hasattr(self, 'selection_label_bg'):
            self.selection_label_bg.pos = self.selection_label.pos
            self.selection_label_bg.size = self.selection_label.size
    
    def _update_chat_scroll_bg(self, *args):
        """更新聊天滚动区域背景"""
        if hasattr(self, 'chat_scroll_bg'):
            self.chat_scroll_bg.pos = self.chat_scroll.pos
            self.chat_scroll_bg.size = self.chat_scroll.size
    
    def _update_chat_container_bg(self, *args):
        """更新聊天容器背景"""
        if hasattr(self, 'chat_container_bg'):
            self.chat_container_bg.pos = self.chat_container.pos
            self.chat_container_bg.size = self.chat_container.size


# 测试应用类
class TestTextInputChatApp(App):
    """测试应用，用于单独运行text_input_chat_screen"""
    
    def build(self):
        from kivy.uix.screenmanager import ScreenManager
        sm = ScreenManager()
        
        # 创建测试屏幕
        test_screen = TextInputChatScreen(name='test_chat')
        sm.add_widget(test_screen)
        
        return sm


if __name__ == '__main__':
    from kivy.core.window import Window
    Window.size = (1200, 800)
    TestTextInputChatApp().run() 