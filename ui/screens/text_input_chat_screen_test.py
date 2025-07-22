"""
文本输入聊天屏幕测试模块
基于TextInputChatScreen，用于测试新功能
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

class TextInputChatScreenTest(Screen):
    """文本输入聊天屏幕测试版本"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history = []
        self.selected_text_backup = ""
        self.is_text_selected = False
        self.selection_start = 0
        self.selection_end = 0
        
        # 文章数据
        self.article_title = "Test Article"
        self.article_content = """The Internet and Language Learning

The internet has revolutionized the way we learn languages. With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.

Online language learning platforms offer a variety of features that traditional classroom settings cannot provide. These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.

One of the most significant advantages of internet-based language learning is the availability of authentic materials. Learners can access real news articles, videos, podcasts, and social media content in their target language.

Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs. Students can connect with peers from different countries, practice conversation skills, and share cultural insights."""
        
        self._setup_ui()
        self._bind_events()
        
        # 选择状态变量
        self.selection_start_index = -1
        self.selection_end_index = -1
        self.is_dragging = False
        self.selected_indices = set()  # 存储所有选中的token索引
        self.last_touch_time = 0  # 记录上次触摸时间，用于判断连续点击
        self.touch_timeout = 0.5  # 连续点击的时间窗口（秒）
    
    def set_article(self, article_data):
        """设置文章数据"""
        if hasattr(article_data, 'text_title'):
            self.article_title = article_data.text_title
        else:
            self.article_title = "Test Article"
        
        if hasattr(article_data, 'text_by_sentence'):
            # 将句子列表转换为文本
            sentences = []
            for sentence in article_data.text_by_sentence:
                sentences.append(sentence.sentence_body)
            self.article_content = " ".join(sentences)
        else:
            self.article_content = "Article content not available."
        
        # 更新UI显示
        self._update_article_display()
        print(f"📖 设置文章: {self.article_title}")
        print(f"📝 文章内容长度: {len(self.article_content)} 字符")
    
    def _update_article_display(self):
        """更新文章显示"""
        if hasattr(self, 'article_title_label'):
            self.article_title_label.text = f'Test Article: {self.article_title}'
        
        # 重新创建文章内容（如果需要）
        if hasattr(self, 'tokens'):
            self._recreate_article_content()
    
    def _tokenize_text(self, text):
        """将文本分词为词/短语"""
        import re
        
        # 使用正则表达式分词
        # 保留标点符号作为单独的token
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        
        # 过滤空token并合并相邻的标点符号
        filtered_tokens = []
        for token in tokens:
            if token.strip():
                filtered_tokens.append(token)
        
        print(f"📝 分词结果: {filtered_tokens}")
        return filtered_tokens
    
    def _recreate_article_content(self):
        """重新创建文章内容"""
        # 清除现有内容
        if hasattr(self, 'article_content_container'):
            self.article_content_container.clear_widgets()
        
        # 重新分词
        self.tokens = self._tokenize_text(self.article_content)
        self.token_widgets = []
        
        # 重新创建token标签
        current_line = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=5)
        line_width = 0
        
        for i, token in enumerate(self.tokens):
            token_label = Label(
                text=token,
                size_hint=(None, None),
                size=(len(token) * 30, 50),
                color=(0.2, 0.2, 0.2, 1),
                font_size=48,
                halign='left',
                valign='middle',
                padding=(5, 5)
            )
            
            with token_label.canvas.before:
                Color(1, 1, 1, 1)
                self.token_bg = Rectangle(pos=token_label.pos, size=token_label.size)
            
            token_label.bind(
                pos=self._update_token_bg,
                size=self._update_token_bg,
                on_touch_down=self._on_token_touch_down,
                on_touch_move=self._on_token_touch_move,
                on_touch_up=self._on_token_touch_up
            )
            
            token_label.token_index = i
            token_label.token_text = token
            token_label.is_selected = False
            
            self.token_widgets.append(token_label)
            
            if line_width + len(token) * 30 > 1200:
                self.article_content_container.add_widget(current_line)
                current_line = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=5)
                line_width = 0
            
            current_line.add_widget(token_label)
            line_width += len(token) * 30 + 5
        
        if current_line.children:
            self.article_content_container.add_widget(current_line)
        
        self.article_content_container.height = len(self.article_content_container.children) * 65
    
    def _go_back(self, instance):
        """返回主页面"""
        print("⬅️ 返回主页面")
        if self.manager:
            self.manager.current = "main"
    
    def _setup_ui(self):
        """设置UI界面"""
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 上方：文章阅读区域
        reading_panel = self._create_reading_panel()
        main_layout.add_widget(reading_panel)
        
        # 下方：聊天区域
        chat_panel = self._create_chat_panel()
        main_layout.add_widget(chat_panel)
        
        self.add_widget(main_layout)
    
    def _create_reading_panel(self):
        """创建文章阅读面板"""
        reading_panel = BoxLayout(orientation='vertical', size_hint_y=0.6, spacing=10)
        
        # 顶部栏（返回按钮 + 文章标题）
        top_bar = self._create_top_bar()
        reading_panel.add_widget(top_bar)
        
        # 文章内容
        article_content = self._create_article_content()
        reading_panel.add_widget(article_content)
        
        # 选择状态标签
        selection_label = self._create_selection_label()
        reading_panel.add_widget(selection_label)
        
        return reading_panel
    
    def _create_top_bar(self):
        """创建顶部栏"""
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        # 返回按钮
        back_btn = Button(
            text='← Back',
            size_hint_x=None,
            width=100,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        back_btn.bind(on_press=self._go_back)
        
        # 文章标题
        self.article_title_label = Label(
            text='Test Article: Article Title',
            size_hint_x=1,
            color=(0.2, 0.2, 0.2, 1),
            font_size=18,
            bold=True,
            halign='left',
            valign='middle'
        )
        
        top_bar.add_widget(back_btn)
        top_bar.add_widget(self.article_title_label)
        
        return top_bar
    
    def _create_article_title(self):
        """创建文章标题"""
        title_label = Label(
            text='Test Article: Article Title',
            size_hint_y=None,
            height=40,
            color=(0.2, 0.2, 0.2, 1),
            font_size=18,
            bold=True,
            halign='left',
            valign='middle'
        )
        return title_label
    
    def _create_article_content(self):
        """创建文章内容区域 - 基于词/短语的选择"""
        # 滚动视图
        scroll_view = ScrollView(size_hint=(1, 1))
        
        # 创建文章内容容器
        self.article_content_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=400,
            padding=(10, 10),
            spacing=5
        )
        
        # 绑定容器的触摸事件，用于点击空白处取消选择
        self.article_content_container.bind(on_touch_down=self._on_container_touch_down)
        
        # 分词并创建可选择的词/短语
        self.tokens = self._tokenize_text(self.article_content)
        self.token_widgets = []
        
        # 创建词/短语标签
        current_line = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=5)
        line_width = 0
        
        for i, token in enumerate(self.tokens):
            # 创建词/短语标签
            token_label = Label(
                text=token,
                size_hint=(None, None),
                size=(len(token) * 30, 50),  # 根据文本长度调整宽度
                color=(0.2, 0.2, 0.2, 1),
                font_size=48,
                halign='left',
                valign='middle',
                padding=(5, 5)
            )
            
            # 为每个词/短语添加背景和点击事件
            with token_label.canvas.before:
                Color(1, 1, 1, 1)  # 白色背景
                self.token_bg = Rectangle(pos=token_label.pos, size=token_label.size)
            
            # 绑定事件
            token_label.bind(
                pos=self._update_token_bg,
                size=self._update_token_bg,
                on_touch_down=self._on_token_touch_down,
                on_touch_move=self._on_token_touch_move,
                on_touch_up=self._on_token_touch_up
            )
            
            # 存储token信息
            token_label.token_index = i
            token_label.token_text = token
            token_label.is_selected = False
            
            self.token_widgets.append(token_label)
            
            # 检查是否需要换行
            if line_width + len(token) * 30 > 1200:  # 假设最大宽度1200
                self.article_content_container.add_widget(current_line)
                current_line = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=5)
                line_width = 0
            
            current_line.add_widget(token_label)
            line_width += len(token) * 30 + 5
        
        # 添加最后一行
        if current_line.children:
            self.article_content_container.add_widget(current_line)
        
        # 设置容器高度
        self.article_content_container.height = len(self.article_content_container.children) * 65
        
        scroll_view.add_widget(self.article_content_container)
        return scroll_view
    
    def _create_selection_label(self):
        """创建选择状态标签"""
        self.selection_label = Label(
            text='No text selected',
            size_hint_y=None,
            height=120,  # 增加高度以适应更大的字体
            color=(0.5, 0.5, 0.5, 1),
            font_size=42,  # 从14放大到42 (约三倍)
            halign='left',
            valign='middle'
        )
        return self.selection_label
    
    def _create_chat_panel(self):
        """创建聊天面板"""
        chat_panel = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=10)
        
        # 聊天标题
        chat_title = self._create_chat_title()
        chat_panel.add_widget(chat_title)
        
        # 聊天滚动区域
        self.chat_scroll, self.chat_container = self._create_chat_scroll_area()
        chat_panel.add_widget(self.chat_scroll)
        
        # 输入区域
        input_layout = self._create_input_layout()
        chat_panel.add_widget(input_layout)
        
        return chat_panel
    
    def _create_chat_title(self):
        """创建聊天标题"""
        title_label = Label(
            text='Test AI Assistant Chat',
            size_hint_y=None,
            height=40,
            color=(0.2, 0.2, 0.2, 1),
            font_size=16,
            bold=True,
            halign='left',
            valign='middle'
        )
        return title_label
    
    def _create_chat_scroll_area(self):
        """创建聊天滚动区域"""
        # 滚动视图
        chat_scroll = ScrollView(size_hint=(1, 1))
        
        # 聊天容器
        chat_container = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=10,
            padding=(10, 10)
        )
        
        # 设置背景
        with chat_container.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.chat_container_bg = Rectangle(pos=chat_container.pos, size=chat_container.size)
        chat_container.bind(pos=self._update_chat_container_bg, size=self._update_chat_container_bg)
        chat_container.bind(minimum_height=lambda instance, value: setattr(chat_container, 'height', value))
        
        chat_scroll.add_widget(chat_container)
        return chat_scroll, chat_container
    
    def _create_input_layout(self):
        """创建输入布局"""
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        # 输入框
        self.chat_input = TextInput(
            text='',
            size_hint_x=0.8,
            multiline=False,
            background_color=(1, 1, 1, 1),
            foreground_color=(0.2, 0.2, 0.2, 1),
            font_size=16,
            padding=(10, 10),
            hint_text='Type your message here...'
        )
        self.chat_input.bind(on_text_validate=self._on_send_message)
        
        # 发送按钮
        send_btn = Button(
            text='Send',
            size_hint_x=0.2,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        send_btn.bind(on_press=self._on_send_message)
        
        input_layout.add_widget(self.chat_input)
        input_layout.add_widget(send_btn)
        
        return input_layout
    
    def _bind_events(self):
        """绑定事件"""
        # 添加欢迎消息
        Clock.schedule_once(lambda dt: self._add_chat_message("Test AI Assistant", "Hello! I'm here to help you with language learning. You can select any text from the article and ask me questions about it.", is_ai=True), 0.5)
    
    def _block_input(self, text, from_undo):
        """阻止输入（用于只读文本）"""
        return False
    
    def _on_chat_input_focus(self, instance, value):
        """聊天输入框焦点事件"""
        if value:  # 获得焦点
            # 使用token选择机制，保持当前选择状态
            if self.selected_text_backup and self.is_text_selected:
                print(f"🎯 输入框获得焦点，保持选中文本: '{self.selected_text_backup}'")
            else:
                print("🎯 输入框获得焦点，没有选中文本")
        else:  # 失去焦点
            print(f"🎯 输入框失去焦点，当前选中文本: '{self.selected_text_backup}'")
    
    def _on_text_selection_change(self, instance, value):
        """文本选择变化事件（保留用于兼容性）"""
        # 这个方法现在主要用于兼容性，实际选择由token机制处理
        pass
    
    def _update_selection_display(self, dt=None):
        """更新选择状态显示"""
        # 使用token选择机制
        has_backup = self.selected_text_backup and self.is_text_selected
        
        if has_backup:
            # 有选中的文本
            selected_text = self.selected_text_backup[:50] + "..." if len(self.selected_text_backup) > 50 else self.selected_text_backup
            self.selection_label.text = f'Selected: "{selected_text}"'
            self.selection_label.color = (0.2, 0.6, 1, 1)
            print(f"📝 显示选择: '{selected_text}'")
        else:
            # 没有任何选择
            self.selected_text_backup = ""
            self.is_text_selected = False
            self._update_selection_display()
    
    def _get_selected_text(self):
        """获取当前选中的文本"""
        # 使用token选择机制
        if self.selected_text_backup and self.is_text_selected:
            return self.selected_text_backup
        return ""
    
    def _keep_text_highlighted(self):
        """保持文本高亮"""
        # 这里可以添加保持文本高亮的逻辑
        pass
    
    def _force_selection_update(self, dt):
        """强制更新选择状态"""
        # 这里可以添加强制更新选择状态的逻辑
        pass
    
    def _on_send_message(self, *args):
        """发送消息"""
        message = self.chat_input.text.strip()
        if not message:
            return
        
        # 获取选中的文本
        selected_text = self._get_selected_text()
        
        # 添加用户消息
        if selected_text:
            self._add_chat_message("You", message, is_ai=False, quoted_text=selected_text)
        else:
            self._add_chat_message("You", message, is_ai=False)
        
        # 生成AI回复
        ai_response = self._generate_ai_response(message, selected_text)
        self._add_chat_message("Test AI Assistant", ai_response, is_ai=True)
        
        # 清空输入
        self.chat_input.text = ''
    
    def _add_chat_message(self, sender, message, is_ai=False, quoted_text=None):
        """添加聊天消息到界面"""
        # 创建消息容器
        message_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=160, padding=10)
        
        # 发送者标签
        sender_label = Label(
            text=sender,
            size_hint_y=None,
            height=40,
            color=(0.6, 0.6, 0.6, 1) if is_ai else (0.2, 0.6, 1, 1),
            halign='left',
            font_size=28
        )
        message_layout.add_widget(sender_label)
        
        # 如果有引用的文本，显示引用格式
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
    
    def _generate_ai_response(self, user_message, selected_text):
        """生成AI回复 - 测试版本"""
        # 测试版本的AI回复逻辑
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
    
    def backup_selected_text(self):
        """备份选中的文本"""
        if self.article_content_widget.selection_text:
            self.selected_text_backup = self.article_content_widget.selection_text
            self.is_text_selected = True
            print(f"📝 备份选中文本: '{self.selected_text_backup[:30]}...'")
        elif self.selected_text_backup and self.is_text_selected:
            # 如果当前没有选择但有备份，保持备份状态
            print(f"📝 保持备份文本: '{self.selected_text_backup[:30]}...'")
        else:
            # 没有选择也没有备份
            self.selected_text_backup = ""
            self.is_text_selected = False
            print("📝 没有选中文本")
    
    def clear_text_selection(self):
        """清除文本选择"""
        self.selected_text_backup = ""
        self.is_text_selected = False
        print("📝 清除文本选择")
    
    # 背景更新方法
    def _update_article_title_bg(self, *args):
        if hasattr(self, 'article_title_bg'):
            self.article_title_bg.pos = args[0].pos
            self.article_title_bg.size = args[0].size
    
    def _update_chat_title_bg(self, *args):
        if hasattr(self, 'chat_title_bg'):
            self.chat_title_bg.pos = args[0].pos
            self.chat_title_bg.size = args[0].size
    
    def _update_selection_label_bg(self, *args):
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
    
    def _update_token_bg(self, instance, value):
        """更新token背景"""
        if hasattr(instance, 'canvas') and instance.canvas.before:
            for instruction in instance.canvas.before.children:
                if isinstance(instruction, Rectangle):
                    instruction.pos = instance.pos
                    instruction.size = instance.size
    
    def _on_token_touch_down(self, instance, touch):
        """token触摸按下事件"""
        if instance.collide_point(*touch.pos):
            import time
            current_time = time.time()
            
            print(f"🎯 触摸token: '{instance.token_text}' (索引: {instance.token_index})")
            
            # 检查是否是连续点击
            is_continuous_click = (current_time - self.last_touch_time) < self.touch_timeout
            
            if is_continuous_click and not self.is_dragging:
                # 连续点击：添加到选择中
                print(f"🎯 连续点击，添加到选择: '{instance.token_text}'")
                self.selected_indices.add(instance.token_index)
                self._highlight_token(instance, True)
            else:
                # 新的选择或拖拽开始
                if not self.is_dragging:
                    # 清除之前的选择
                    self._clear_all_selections()
                    self.selected_indices.clear()
                
                # 开始选择
                self.selection_start_index = instance.token_index
                self.selection_end_index = instance.token_index
                self.is_dragging = True
                self.selected_indices.add(instance.token_index)
                
                # 高亮当前token
                self._highlight_token(instance, True)
            
            # 更新选择状态
            self._update_selection_from_tokens()
            self.last_touch_time = current_time
            
            return True
        return False
    
    def _on_token_touch_move(self, instance, touch):
        """token触摸移动事件"""
        if not self.is_dragging:
            return False
        
        # 找到当前触摸的token
        for token_widget in self.token_widgets:
            if token_widget.collide_point(*touch.pos):
                print(f"🎯 拖拽到token: '{token_widget.token_text}' (索引: {token_widget.token_index})")
                
                # 更新选择范围
                self.selection_end_index = token_widget.token_index
                
                # 计算拖拽范围内的所有索引
                start = min(self.selection_start_index, self.selection_end_index)
                end = max(self.selection_start_index, self.selection_end_index)
                
                # 更新选中索引集合
                self.selected_indices.clear()
                for i in range(start, end + 1):
                    self.selected_indices.add(i)
                
                # 重新高亮选择范围
                self._highlight_selection_range()
                
                # 更新选择状态
                self._update_selection_from_tokens()
                
                return True
        
        return False
    
    def _on_token_touch_up(self, instance, touch):
        """token触摸抬起事件"""
        if self.is_dragging:
            print(f"🎯 结束拖拽，选择范围: {self.selection_start_index} - {self.selection_end_index}")
            print(f"🎯 选中的索引: {sorted(self.selected_indices)}")
            self.is_dragging = False
            
            # 确保选择范围正确（start <= end）
            if self.selection_start_index > self.selection_end_index:
                self.selection_start_index, self.selection_end_index = self.selection_end_index, self.selection_start_index
            
            # 最终更新选择状态
            self._update_selection_from_tokens()
            
            return True
        return False
    
    def _clear_all_selections(self):
        """清除所有选择"""
        for token_widget in self.token_widgets:
            self._highlight_token(token_widget, False)
        self.selected_indices.clear()
        self.selection_start_index = -1
        self.selection_end_index = -1
    
    def _highlight_token(self, token_widget, is_selected):
        """高亮或取消高亮token"""
        token_widget.is_selected = is_selected
        
        # 更新背景颜色
        with token_widget.canvas.before:
            token_widget.canvas.before.clear()
            if is_selected:
                Color(0.2, 0.6, 1, 0.3)  # 蓝色高亮
            else:
                Color(1, 1, 1, 1)  # 白色背景
            Rectangle(pos=token_widget.pos, size=token_widget.size)
    
    def _highlight_selection_range(self):
        """高亮选择范围内的所有token"""
        # 清除所有选择
        for token_widget in self.token_widgets:
            self._highlight_token(token_widget, False)
        
        # 高亮所有选中的token
        for index in self.selected_indices:
            if 0 <= index < len(self.token_widgets):
                self._highlight_token(self.token_widgets[index], True)
    
    def _update_selection_from_tokens(self):
        """从token选择更新选择状态"""
        if self.selected_indices:
            # 构造选中的文本
            selected_tokens = []
            for i in sorted(self.selected_indices):
                if 0 <= i < len(self.tokens):
                    selected_tokens.append(self.tokens[i])
            
            selected_text = " ".join(selected_tokens)
            
            # 更新选择状态
            self.selected_text_backup = selected_text
            self.is_text_selected = True
            
            print(f"📝 更新选择: '{selected_text}' (索引: {sorted(self.selected_indices)})")
            
            # 更新显示
            self._update_selection_display()
        else:
            self.selected_text_backup = ""
            self.is_text_selected = False
            self._update_selection_display()
    
    def _on_container_touch_down(self, instance, touch):
        """容器触摸事件，用于点击空白处取消选择"""
        # 检查是否点击了任何token
        for token_widget in self.token_widgets:
            if token_widget.collide_point(*touch.pos):
                # 点击了token，不处理（由token自己的事件处理）
                return False
        
        # 点击了空白处，清除所有选择
        print("🎯 点击空白处，清除所有选择")
        self._clear_all_selections()
        self._update_selection_from_tokens()
        return True
    
    def test_run(self):
        """测试运行功能 - 使用测试数据运行当前页面"""
        print("🧪 开始测试运行 TextInputChatScreenTest...")
        
        # 设置测试文章数据
        test_article_data = self._create_test_article_data()
        self.set_article(test_article_data)
        
        # 添加一些测试消息
        self._add_test_messages()
        
        print("✅ 测试数据设置完成")
        print("📖 文章标题:", self.article_title)
        print("📝 文章内容长度:", len(self.article_content))
        print("💬 聊天消息数量:", len(self.chat_history))
    
    def _create_test_article_data(self):
        """创建测试文章数据"""
        class TestArticleData:
            def __init__(self):
                self.text_title = "The Internet and Language Learning"
                self.text_by_sentence = [
                    type('MockSentence', (), {'sentence_body': 'The internet has revolutionized the way we learn languages.'})(),
                    type('MockSentence', (), {'sentence_body': 'With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.'})(),
                    type('MockSentence', (), {'sentence_body': 'Online language learning platforms offer a variety of features that traditional classroom settings cannot provide.'})(),
                    type('MockSentence', (), {'sentence_body': 'These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.'})(),
                    type('MockSentence', (), {'sentence_body': 'One of the most significant advantages of internet-based language learning is the availability of authentic materials.'})(),
                    type('MockSentence', (), {'sentence_body': 'Learners can access real news articles, videos, podcasts, and social media content in their target language.'})(),
                    type('MockSentence', (), {'sentence_body': 'Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs.'})(),
                    type('MockSentence', (), {'sentence_body': 'Students can connect with peers from different countries, practice conversation skills, and share cultural insights.'})()
                ]
        
        return TestArticleData()
    
    def _add_test_messages(self):
        """添加测试聊天消息"""
        # 模拟用户选择文本并提问
        test_scenarios = [
            {
                'selected_text': 'revolutionized',
                'user_message': 'What does this word mean?',
                'ai_response': 'revolutionized means "to completely change or transform something in a fundamental way." It comes from the word "revolution" and is often used to describe major technological or social changes.'
            },
            {
                'selected_text': 'the way we learn',
                'user_message': 'What grammar structure is used here?',
                'ai_response': 'This is a noun phrase structure: "the way we learn". Here, "the way" is a noun phrase meaning "the method or manner", and "we learn" is a relative clause that modifies "way". The relative pronoun "that" or "in which" is omitted.'
            },
            {
                'selected_text': '',
                'user_message': 'Can you help me understand this article?',
                'ai_response': 'Of course! This article discusses how the internet has changed language learning. It mentions online platforms, mobile apps, digital resources, and how they make language learning more accessible. Would you like me to explain any specific part in detail?'
            }
        ]
        
        for scenario in test_scenarios:
            # 模拟文本选择
            if scenario['selected_text']:
                self._on_text_selection_change(None, scenario['selected_text'])
                print(f"📝 模拟选择文本: '{scenario['selected_text']}'")
            
            # 添加用户消息
            self._add_chat_message("You", scenario['user_message'], is_ai=False, quoted_text=scenario['selected_text'] if scenario['selected_text'] else None)
            
            # 添加AI回复
            self._add_chat_message("Test AI Assistant", scenario['ai_response'], is_ai=True)
            
            # 清除选择状态
            if scenario['selected_text']:
                self._on_text_selection_change(None, "")
        
        print(f"✅ 添加了 {len(test_scenarios)} 个测试对话场景") 