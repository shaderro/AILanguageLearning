"""
异步版本的Text Input Chat Screen
完整复制原有UI功能，支持文字选择，并添加异步处理
"""

import threading
import queue
import re
import time
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.properties import BooleanProperty, StringProperty

class AsyncTextInputChatScreen(Screen):
    """异步版本的Text Input Chat Screen"""
    
    # Kivy属性，用于UI状态绑定
    is_processing = BooleanProperty(False)
    processing_status = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(" AsyncTextInputChatScreen __init__ started")
        
        # 聊天相关变量
        self.chat_history = []
        self.selected_text_backup = ""
        self.is_text_selected = False
        self.selection_start = 0
        self.selection_end = 0
        
        # 异步处理相关变量
        self.processing_queue = queue.Queue()
        self.processing_thread = None
        self.is_processing_thread_running = False
        
        # 文章数据
        self.article_title = "Test Article"
        self.article_content = """The Internet and Language Learning

The internet has revolutionized the way we learn languages. With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.

Online language learning platforms offer a variety of features that traditional classroom settings cannot provide. These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.

One of the most significant advantages of internet-based language learning is the availability of authentic materials. Learners can access real news articles, videos, podcasts, and social media content in their target language.

Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs. Students can connect with peers from different countries, practice conversation skills, and share cultural insights."""
        
        # 选择状态变量
        self.selection_start_index = -1
        self.selection_end_index = -1
        self.is_dragging = False
        self.selected_indices = set()
        self.last_touch_time = 0
        self.touch_timeout = 0.5
        
        # 智能提问控制相关变量
        self.previous_context_tokens = []
        self.previous_context_sentence = ""
        self.previous_context_sentence_id = -1
        self.last_used_tokens = []
        
        print("📚 Article data set, initializing MainAssistant...")
        self._initialize_main_assistant()
        print("✅ MainAssistant initialization completed")
        
        print("🔧 Setting up UI...")
        self._setup_ui()
        print("🔧 Binding events...")
        self._bind_events()
        
        # 启动异步处理线程
        self._start_processing_thread()
        
        # 启动状态更新定时器
        Clock.schedule_interval(self._update_processing_status, 0.1)
    
    def _initialize_main_assistant(self):
        """初始化MainAssistant和DataController"""
        try:
            print("🤖 Starting MainAssistant initialization...")
            
            from assistants.main_assistant import MainAssistant
            from data_managers import data_controller
            print("✅ All imports successful")
            
            # 创建DataController实例
            print("🔧 Creating DataController...")
            self.data_controller = data_controller.DataController(max_turns=100)
            print("✅ DataController created")
            
            # 加载现有数据
            try:
                print("📂 Loading existing data...")
                self.data_controller.load_data(
                    grammar_path='data/grammar_rules.json',
                    vocab_path='data/vocab_expressions.json',
                    text_path='data/original_texts.json',
                    dialogue_record_path='data/dialogue_record.json',
                    dialogue_history_path='data/dialogue_history.json'
                )
                print("✅ Successfully loaded existing data")
            except FileNotFoundError as e:
                print(f"⚠️ Some data files not found, starting with empty data: {e}")
            except Exception as e:
                print(f"⚠️ Error loading data, starting with empty data: {e}")
            
            # 创建MainAssistant实例
            print("🔧 Creating MainAssistant...")
            self.main_assistant = MainAssistant(data_controller_instance=self.data_controller)
            print("✅ MainAssistant created successfully")
            
        except Exception as e:
            print(f"❌ Error initializing MainAssistant: {e}")
            self.main_assistant = None
    
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
        self.article_content_container.bind(
            on_touch_down=self._on_container_touch_down,
            on_touch_move=self._on_container_touch_move,
            on_touch_up=self._on_container_touch_up
        )
        
        # 分词并创建可选择的词/短语
        self.tokens, self.sentence_boundaries = self._tokenize_text(self.article_content)
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
            font_size=18,
            bold=True,
            halign='left',
            valign='middle'
        )
        return title_label
    
    def _create_chat_scroll_area(self):
        """创建聊天滚动区域"""
        chat_scroll = ScrollView(size_hint=(1, 1))
        
        self.chat_container = GridLayout(
            cols=1,
            spacing=10,
            size_hint_y=None,
            height=400
        )
        self.chat_container.bind(minimum_height=self.chat_container.setter('height'))
        
        chat_scroll.add_widget(self.chat_container)
        return chat_scroll, self.chat_container
    
    def _create_input_layout(self):
        """创建输入区域"""
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
        
        # 聊天输入框
        self.chat_input = TextInput(
            multiline=False,
            size_hint_x=0.7,
            font_size=24,
            hint_text='Type your question here...'
        )
        input_layout.add_widget(self.chat_input)
        
        # 发送按钮
        self.send_button = Button(
            text='Send',
            size_hint_x=0.3,
            font_size=24
        )
        self.send_button.bind(on_press=self._on_send_message)
        input_layout.add_widget(self.send_button)
        
        return input_layout
    
    def _bind_events(self):
        """绑定事件"""
        if hasattr(self, 'chat_input'):
            self.chat_input.bind(on_text_validate=self._on_send_message)
    
    def _tokenize_text(self, text):
        """分词文本，将标点符号与相邻单词合并，并按句子分组"""
        # 定义标点符号类别
        # 后置标点：应与前一个单词合并
        post_punctuation = r'[,\.!…?\)\]\}""'']'
        # 前置标点：应与后一个单词合并
        pre_punctuation = r'[\(\[\{"'']'
        
        # 步骤1：按句子分割文本
        sentence_endings = r'[。！？\.!?\n]'
        sentences = re.split(f'({sentence_endings})', text)
        
        # 重新组合句子，保留句子结束标点
        sentence_blocks = []
        current_sentence = ""
        for i, part in enumerate(sentences):
            if re.match(sentence_endings, part):
                # 这是句子结束标点
                current_sentence += part
                if current_sentence.strip():
                    sentence_blocks.append(current_sentence.strip())
                current_sentence = ""
            else:
                current_sentence += part
        
        # 添加最后一个句子（如果没有结束标点）
        if current_sentence.strip():
            sentence_blocks.append(current_sentence.strip())
        
        # 步骤2：对每个句子进行分词
        all_tokens = []
        sentence_boundaries = []
        token_index = 0
        
        for sentence_id, sentence in enumerate(sentence_blocks):
            sentence_start_index = token_index
            
            # 分割句子为单词
            words = re.findall(r'\b\w+\b|[^\w\s]', sentence)
            
            # 处理标点符号合并
            processed_words = []
            i = 0
            while i < len(words):
                current_word = words[i]
                
                # 检查是否有前置标点
                if i > 0 and re.match(pre_punctuation, current_word):
                    # 前置标点与下一个单词合并
                    if i + 1 < len(words):
                        processed_words.append(current_word + words[i + 1])
                        i += 2
                    else:
                        processed_words.append(current_word)
                        i += 1
                # 检查是否有后置标点
                elif i + 1 < len(words) and re.match(post_punctuation, words[i + 1]):
                    # 后置标点与前一个单词合并
                    processed_words.append(current_word + words[i + 1])
                    i += 2
                else:
                    processed_words.append(current_word)
                    i += 1
            
            # 添加到所有tokens
            all_tokens.extend(processed_words)
            
            # 记录句子边界
            sentence_end_index = token_index + len(processed_words) - 1
            sentence_boundaries.append({
                'sentence_id': sentence_id,
                'start': sentence_start_index,
                'end': sentence_end_index,
                'text': sentence
            })
            
            token_index += len(processed_words)
        
        return all_tokens, sentence_boundaries
    
    def _on_token_touch_down(self, instance, touch):
        """token触摸按下事件"""
        print(f" Token touch down - '{instance.token_text}' (index: {instance.token_index}), position: {touch.pos}")
        
        # 如果触摸事件已经被其他组件抓取，不处理
        if touch.grab_current is not None:
            print(f"🔍 Touch event already grabbed: {touch.grab_current}, not processing")
            return False
        
        if instance.collide_point(*touch.pos):
            current_time = time.time()
            
            print(f"🎯 Touched token: '{instance.token_text}' (index: {instance.token_index})")
            print(f" Current drag state: {self.is_dragging}, grab state: {touch.grab_current}")
            
            # 检查是否是连续点击
            is_continuous_click = (current_time - self.last_touch_time) < self.touch_timeout
            
            if is_continuous_click and not self.is_dragging:
                # 连续点击：添加到选择中（需要检查句子边界）
                if self._check_sentence_boundary(instance.token_index):
                    print(f"🎯 Continuous click, adding to selection: '{instance.token_text}'")
                    self.selected_indices.add(instance.token_index)
                    self._highlight_token(instance, True)
                else:
                    print("⚠️ Cross-sentence selection prevented")
                    self._show_sentence_boundary_warning()
            else:
                # 新的选择或拖拽开始
                if not self.is_dragging:
                    # 清除之前的选择
                    print("🔍 Starting new selection, clearing previous selection")
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
            
            # 抓取触摸事件
            touch.grab(instance)
            print(f"🔍 Token grabbed touch event: {touch.grab_current}")
            return True
        
        print(f"🔍 Token touch position mismatch, not processing")
        return False
    
    def _on_token_touch_move(self, instance, touch):
        """token触摸移动事件"""
        print(f" Token touch move - '{instance.token_text}' (index: {instance.token_index}), position: {touch.pos}")
        
        # 检查触摸事件是否被当前token抓取
        if touch.grab_current != instance:
            print(" Token did not grab touch event, not processing")
            return False
        
        if not self.is_dragging:
            print(" Not in drag state, not processing")
            return False
        
        # 找到当前触摸的token
        for token_widget in self.token_widgets:
            if token_widget.collide_point(*touch.pos):
                print(f"🎯 Dragged to token: '{token_widget.token_text}' (index: {token_widget.token_index})")
                
                # 检查句子边界
                if self._check_sentence_boundary(token_widget.token_index):
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
                else:
                    print("⚠️ Cross-sentence drag prevented")
                    self._show_sentence_boundary_warning()
                
                return True
        
        # 如果没有找到token，但正在拖拽，也要处理
        if self.is_dragging:
            print("🎯 Dragged to blank area")
            return True
        
        print("🔍 Drag state but no token found, not processing")
        return False
    
    def _on_token_touch_up(self, instance, touch):
        """token触摸抬起事件"""
        print(f"🔍 Token touch up - '{instance.token_text}' (index: {instance.token_index}), position: {touch.pos}")
        
        # 检查触摸事件是否被当前token抓取
        if touch.grab_current != instance:
            print(" Token did not grab touch event, not processing")
            return False
        
        if self.is_dragging:
            print(f"🎯 Ending drag, selection range: {self.selection_start_index} - {self.selection_end_index}")
            print(f"🎯 Selected indices: {sorted(self.selected_indices)}")
            self.is_dragging = False
            
            # 确保选择范围正确（start <= end）
            if self.selection_start_index > self.selection_end_index:
                self.selection_start_index, self.selection_end_index = self.selection_end_index, self.selection_start_index
            
            # 最终更新选择状态
            self._update_selection_from_tokens()
            
            # 释放触摸抓取
            touch.ungrab(instance)
            print("🔍 Token released touch grab (drag ended)")
            return True
        
        # 释放触摸抓取
        touch.ungrab(instance)
        print("🔍 Token released touch grab (non-drag)")
        return False
    
    def _on_container_touch_down(self, instance, touch):
        """容器触摸按下事件"""
        # 检查是否点击了空白区域
        for child in instance.children:
            if child.collide_point(*touch.pos):
                return False
        
        # 点击了空白区域，清除选择
        print("🔍 Container touch down on blank area, clearing selection")
        self._clear_all_selections()
        self._update_selection_from_tokens()
        return True
    
    def _on_container_touch_move(self, instance, touch):
        """容器触摸移动事件"""
        return False
    
    def _on_container_touch_up(self, instance, touch):
        """容器触摸抬起事件"""
        return False
    
    def _clear_all_selections(self):
        """清除所有选择"""
        print(f"🔍 Clearing all selections - current state: drag={self.is_dragging}, selected indices={sorted(self.selected_indices)}")
        
        for token_widget in self.token_widgets:
            self._highlight_token(token_widget, False)
        self.selected_indices.clear()
        self.selection_start_index = -1
        self.selection_end_index = -1
        # 重置拖拽状态
        self.is_dragging = False
        
        print(f"🔍 Clearing complete - new state: drag={self.is_dragging}, selected indices={sorted(self.selected_indices)}")
    
    def _highlight_token(self, token_widget, is_selected):
        """高亮或取消高亮token"""
        token_widget.is_selected = is_selected
        
        # 更新背景颜色
        if hasattr(token_widget, 'token_bg'):
            # 清除现有的背景
            token_widget.canvas.before.clear()
            
            # 重新创建背景
            with token_widget.canvas.before:
                if is_selected:
                    Color(0.2, 0.6, 1, 0.3)  # 蓝色高亮
                else:
                    Color(1, 1, 1, 1)  # 白色背景
                token_widget.token_bg = Rectangle(pos=token_widget.pos, size=token_widget.size)
    
    def _highlight_selection_range(self):
        """高亮选择范围内的所有token"""
        # 清除所有选择
        for token_widget in self.token_widgets:
            self._highlight_token(token_widget, False)
        
        # 高亮所有选中的token
        for index in self.selected_indices:
            if 0 <= index < len(self.token_widgets):
                self._highlight_token(self.token_widgets[index], True)
    
    def _check_sentence_boundary(self, token_index):
        """检查token是否在同一个句子内"""
        if not self.selected_indices:
            return True
        
        # 找到第一个选中token所属的句子
        first_selected = min(self.selected_indices)
        target_sentence = None
        
        for boundary in self.sentence_boundaries:
            if boundary['start'] <= first_selected <= boundary['end']:
                target_sentence = boundary
                break
        
        if target_sentence is None:
            return True
        
        # 检查新token是否在同一句子内
        return target_sentence['start'] <= token_index <= target_sentence['end']
    
    def _show_sentence_boundary_warning(self):
        """显示跨句子选择警告"""
        warning_message = "⚠️ Please select tokens within the same sentence"
        print(f"🚫 {warning_message}")
        self._add_chat_message("System", warning_message, is_ai=True)
    
    def _update_selection_from_tokens(self):
        """根据选中的tokens更新选择显示"""
        if not self.selected_indices:
            self.selection_label.text = 'No text selected'
            return
        
        # 获取选中的文本
        selected_tokens = []
        for index in sorted(self.selected_indices):
            if 0 <= index < len(self.tokens):
                selected_tokens.append(self.tokens[index])
        
        selected_text = " ".join(selected_tokens)
        self.selection_label.text = f'Selected: {selected_text}'
        
        print(f" Selection updated: {selected_text}")
    
    def _get_selected_text(self):
        """获取选中的文本"""
        if not self.selected_indices:
            return ""
        
        selected_tokens = []
        for i in sorted(self.selected_indices):
            if 0 <= i < len(self.tokens):
                selected_tokens.append(self.tokens[i])
        
        return " ".join(selected_tokens)
    
    def _get_full_sentence_info(self, token_indices):
        """根据token索引获取完整句子信息"""
        if not token_indices or not hasattr(self, 'sentence_boundaries'):
            return None
        
        # 找到第一个token所属的句子
        first_token_index = min(token_indices)
        sentence_info = None
        
        for boundary in self.sentence_boundaries:
            if boundary['start'] <= first_token_index <= boundary['end']:
                sentence_info = boundary
                break
        
        return sentence_info
    
    def _update_token_bg(self, instance, value):
        """更新token背景"""
        if hasattr(instance, 'token_bg'):
            instance.token_bg.pos = instance.pos
            instance.token_bg.size = instance.size
    
    def _go_back(self, instance):
        """返回按钮事件"""
        print("🔙 Back button pressed")
        # 这里可以添加返回逻辑
    
    # 异步处理相关方法
    def _start_processing_thread(self):
        """启动异步处理线程"""
        if not self.is_processing_thread_running:
            self.is_processing_thread_running = True
            self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
            self.processing_thread.start()
            print("🔄 Started async processing thread")
    
    def _processing_worker(self):
        """异步处理工作线程"""
        while self.is_processing_thread_running:
            try:
                # 从队列获取任务
                task = self.processing_queue.get(timeout=1.0)
                if task is None:  # 停止信号
                    break
                
                # 处理任务
                self._process_task(task)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error in processing worker: {e}")
                # 发送错误响应到主线程
                self._send_error_response(str(e))
    
    def _process_task(self, task):
        """处理单个任务"""
        try:
            task_type = task.get('type')
            
            if task_type == 'main_assistant':
                # 处理MainAssistant任务
                self._process_main_assistant_task(task)
            elif task_type == 'post_processing':
                # 处理后续任务
                self._process_post_processing_task(task)
            else:
                print(f"⚠️ Unknown task type: {task_type}")
                
        except Exception as e:
            print(f"❌ Error processing task: {e}")
            self._send_error_response(str(e))
    
    def _process_main_assistant_task(self, task):
        """处理MainAssistant任务"""
        try:
            sentence_object = task['sentence_object']
            user_question = task['user_question']
            selected_tokens = task['selected_tokens']
            
            print("🤖 Processing MainAssistant task...")
            
            # 更新处理状态
            self._update_processing_status_async("Processing AI response...")
            
            # 调用MainAssistant
            quoted_string = " ".join(selected_tokens) if selected_tokens else None
            
            self.main_assistant.run(
                quoted_sentence=sentence_object,
                user_question=user_question,
                quoted_string=quoted_string
            )
            
            # 获取AI响应
            ai_response = self.main_assistant.session_state.current_response
            if not ai_response:
                ai_response = self._generate_fallback_response(user_question, sentence_object.sentence_body)
            
            # 发送响应到主线程
            self._send_ai_response(ai_response)
            
            # 添加后续处理任务
            self._add_post_processing_task(sentence_object, user_question, selected_tokens)
            
        except Exception as e:
            print(f"❌ Error in MainAssistant processing: {e}")
            self._send_error_response(str(e))
    
    def _process_post_processing_task(self, task):
        """处理后续任务（语法、词汇处理等）"""
        try:
            sentence_object = task['sentence_object']
            user_question = task['user_question']
            selected_tokens = task['selected_tokens']
            
            print("🔄 Processing post-processing tasks...")
            
            # 更新处理状态
            self._update_processing_status_async("Processing grammar and vocabulary...")
            
            # 这里可以添加其他异步处理逻辑
            # 比如语法规则比较、词汇分析等
            
            # 保存数据
            self._save_data_async()
            
            # 更新处理状态
            self._update_processing_status_async("Completed")
            
        except Exception as e:
            print(f"❌ Error in post-processing: {e}")
    
    def _add_post_processing_task(self, sentence_object, user_question, selected_tokens):
        """添加后续处理任务"""
        task = {
            'type': 'post_processing',
            'sentence_object': sentence_object,
            'user_question': user_question,
            'selected_tokens': selected_tokens
        }
        self.processing_queue.put(task)
    
    def _send_ai_response(self, ai_response):
        """发送AI响应到主线程"""
        Clock.schedule_once(lambda dt: self._handle_ai_response(ai_response), 0)
    
    def _send_error_response(self, error_message):
        """发送错误响应到主线程"""
        Clock.schedule_once(lambda dt: self._handle_error_response(error_message), 0)
    
    def _update_processing_status_async(self, status):
        """异步更新处理状态"""
        Clock.schedule_once(lambda dt: setattr(self, 'processing_status', status), 0)
    
    def _handle_ai_response(self, ai_response):
        """在主线程中处理AI响应"""
        # 添加AI消息到聊天界面
        self._add_chat_message("AI Assistant", ai_response, is_ai=True)
        
        # 恢复UI交互
        self._restore_ui_interaction()
        
        print("✅ AI response handled successfully")
    
    def _handle_error_response(self, error_message):
        """在主线程中处理错误响应"""
        # 添加错误消息到聊天界面
        self._add_chat_message("System", f"Error: {error_message}", is_ai=True)
        
        # 恢复UI交互
        self._restore_ui_interaction()
        
        print(f"❌ Error response handled: {error_message}")
    
    def _restore_ui_interaction(self):
        """恢复UI交互"""
        self.is_processing = False
        self.processing_status = ""
        
        # 恢复输入框和发送按钮
        if hasattr(self, 'chat_input'):
            self.chat_input.disabled = False
        if hasattr(self, 'send_button'):
            self.send_button.disabled = False
        
        print("🔄 UI interaction restored")
    
    def _disable_ui_interaction(self):
        """禁用UI交互"""
        self.is_processing = True
        self.processing_status = "Processing..."
        
        # 禁用输入框和发送按钮
        if hasattr(self, 'chat_input'):
            self.chat_input.disabled = True
        if hasattr(self, 'send_button'):
            self.send_button.disabled = True
        
        print("⏸️ UI interaction disabled")
    
    def _update_processing_status(self, dt):
        """更新处理状态显示"""
        if hasattr(self, 'status_label') and self.is_processing:
            self.status_label.text = self.processing_status
    
    def _on_send_message(self, *args):
        """发送消息 - 异步版本"""
        message = self.chat_input.text.strip()
        if not message:
            return
        
        # 检查是否正在处理中
        if self.is_processing:
            print("⚠️ Already processing, please wait...")
            return
        
        # 获取当前选中的文本和tokens
        selected_text = self._get_selected_text()
        current_selected_tokens = []
        current_sentence_info = None
        
        if selected_text and self.selected_indices:
            # 构造当前选中的tokens
            for i in sorted(self.selected_indices):
                if 0 <= i < len(self.tokens):
                    current_selected_tokens.append(self.tokens[i])
            
            # 获取当前句子的完整信息
            current_sentence_info = self._get_full_sentence_info(self.selected_indices)
        
        # 智能提问控制逻辑
        context_tokens = []
        context_sentence = ""
        context_sentence_id = -1
        is_follow_up = False
        
        if current_selected_tokens:
            # 情况1：当前轮用户有选中token
            print("🎯 Using current selected tokens as context")
            context_tokens = current_selected_tokens
            context_sentence = current_sentence_info['text'] if current_sentence_info else ""
            context_sentence_id = current_sentence_info['sentence_id'] if current_sentence_info else -1
            
            # 更新上一轮上下文
            self.previous_context_tokens = context_tokens.copy()
            self.previous_context_sentence = context_sentence
            self.previous_context_sentence_id = context_sentence_id
            self.last_used_tokens = context_tokens.copy()
            
        elif self.previous_context_tokens:
            # 情况2：上一轮对话中存在选中的token，视为follow-up question
            print("🔄 Inheriting previous round sentence reference, treating as follow-up question")
            context_tokens = self.previous_context_tokens
            context_sentence = self.previous_context_sentence
            context_sentence_id = self.previous_context_sentence_id
            is_follow_up = True
            
        else:
            # 情况3：禁止提问，提示用户选择句子
            print("⚠️ Prohibit question: No selected sentence and no previous context")
            self._show_selection_required_warning()
            return
        
        # 添加用户消息到聊天界面
        if context_sentence:
            quoted_text = context_sentence
            if is_follow_up:
                quoted_text = f"[Follow-up] {context_sentence}"
            self._add_chat_message("You", message, is_ai=False, quoted_text=quoted_text)
        else:
            self._add_chat_message("You", message, is_ai=False)
        
        # 禁用UI交互
        self._disable_ui_interaction()
        
        # 转换为Sentence对象
        sentence_object = self._convert_to_sentence_object(
            context_tokens, 
            context_sentence, 
            context_sentence_id, 
            message
        )
        
        # 添加异步任务
        task = {
            'type': 'main_assistant',
            'sentence_object': sentence_object,
            'user_question': message,
            'selected_tokens': context_tokens
        }
        self.processing_queue.put(task)
        
        # 清空输入
        self.chat_input.text = ''
        
        print("🚀 Async task added to processing queue")
    
    def _show_selection_required_warning(self):
        """显示需要选择句子的警告"""
        warning_message = "⚠️ Please select a relevant sentence before asking a question"
        print(f"🚫 {warning_message}")
        
        self._add_chat_message("System", warning_message, is_ai=True)
    
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
        
        # 引用文本（如果有）
        if quoted_text:
            quoted_label = Label(
                text=f"Quote: {quoted_text[:100]}{'...' if len(quoted_text) > 100 else ''}",
                size_hint_y=None,
                height=30,
                color=(0.8, 0.8, 0.8, 1),
                halign='left',
                font_size=20
            )
            message_layout.add_widget(quoted_label)
        
        # 消息内容
        message_label = Label(
            text=message,
            size_hint_y=None,
            height=80,
            color=(0.2, 0.2, 0.2, 1),
            halign='left',
            valign='top',
            text_size=(None, None),
            font_size=24
        )
        message_layout.add_widget(message_label)
        
        # 添加到聊天历史
        self.chat_history.append(message_layout)
        
        # 添加到UI（如果UI已初始化）
        if hasattr(self, 'chat_container'):
            self.chat_container.add_widget(message_layout)
            # 滚动到底部
            Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
    
    def _scroll_to_bottom(self):
        """滚动到底部"""
        if hasattr(self, 'chat_scroll'):
            self.chat_scroll.scroll_y = 0
    
    def _convert_to_sentence_object(self, selected_tokens, full_sentence, sentence_id, user_input):
        """转换为Sentence对象"""
        from data_managers.data_classes import Sentence
        
        return Sentence(
            text_id=0,  # 可以根据实际情况设置
            sentence_id=sentence_id if sentence_id >= 0 else 0,
            sentence_body=full_sentence,
            grammar_annotations=[],
            vocab_annotations=[]
        )
    
    def _generate_fallback_response(self, user_question, sentence_body):
        """生成备用响应"""
        if sentence_body:
            return f"Fallback response: I understand you're asking about '{sentence_body[:50]}...'. This is a fallback response as the AI assistant is not fully available."
        else:
            return "Fallback response: I'm here to help with language learning. Please select some text and ask me questions about grammar, vocabulary, or meaning."
    
    def _save_data_async(self):
        """异步保存数据"""
        try:
            if hasattr(self, 'data_controller'):
                self.data_controller.save_data(
                    grammar_path='data/grammar_rules.json',
                    vocab_path='data/vocab_expressions.json',
                    text_path='data/original_texts.json',
                    dialogue_record_path='data/dialogue_record.json',
                    dialogue_history_path='data/dialogue_history.json'
                )
                print("✅ Data saved successfully")
        except Exception as e:
            print(f"❌ Error saving data: {e}")
    
    def on_stop(self):
        """停止时清理资源"""
        self.is_processing_thread_running = False
        if self.processing_thread:
            self.processing_queue.put(None)  # 发送停止信号
            self.processing_thread.join(timeout=2.0)
        print("🛑 Async processing thread stopped")
    
    def test_run(self):
        """测试运行"""
        print(" Running async chat screen test...")
        
        # 添加一些测试消息
        self._add_chat_message("System", "Welcome to the async chat interface!", is_ai=True)
        self._add_chat_message("System", "Select some text and ask questions about grammar or vocabulary.", is_ai=True)
        
        print("✅ Async chat screen test completed") 