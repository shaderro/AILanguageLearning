"""
Text Input Chat Screen Test Module
Based on TextInputChatScreen, used for testing new features
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
    """Text Input Chat Screen Test Version"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("🚀 TextInputChatScreenTest __init__ started")
        
        self.chat_history = []
        self.selected_text_backup = ""
        self.is_text_selected = False
        self.selection_start = 0
        self.selection_end = 0
        
        # Article data
        self.article_title = "Test Article"
        self.article_content = """The Internet and Language Learning

The internet has revolutionized the way we learn languages. With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.

Online language learning platforms offer a variety of features that traditional classroom settings cannot provide. These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.

One of the most significant advantages of internet-based language learning is the availability of authentic materials. Learners can access real news articles, videos, podcasts, and social media content in their target language.

Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs. Students can connect with peers from different countries, practice conversation skills, and share cultural insights."""
        
        print("📚 Article data set, initializing MainAssistant...")
        # Initialize MainAssistant and DataController
        self._initialize_main_assistant()
        print("✅ MainAssistant initialization completed")
        
        print("🔧 Setting up UI...")
        self._setup_ui()
        print("🔧 Binding events...")
        self._bind_events()
        
        # Selection state variables
        self.selection_start_index = -1
        self.selection_end_index = -1
        self.is_dragging = False
        self.selected_indices = set()  # Store all selected token indices
        self.last_touch_time = 0  # Record last touch time for continuous click detection
        self.touch_timeout = 0.5  # Continuous click time window (seconds)
        
        # New: Smart question control related variables
        self.previous_context_tokens = []  # Previous conversation context sentence tokens
        self.previous_context_sentence = ""  # Previous conversation complete sentence
        self.previous_context_sentence_id = -1  # Previous conversation sentence ID
        self.last_used_tokens = []  # Recently used tokens (for follow-up questions)
    
    def _initialize_main_assistant(self):
        """Initialize MainAssistant and DataController"""
        try:
            print("🤖 Starting MainAssistant initialization...")
            
            # Import required modules
            print("📦 Importing MainAssistant...")
            from assistants.main_assistant import MainAssistant
            print("📦 Importing DataController...")
            from data_managers import data_controller
            print("✅ All imports successful")
            
            # Create DataController instance
            print("🔧 Creating DataController...")
            self.data_controller = data_controller.DataController(max_turns=100)
            print("✅ DataController created")
            
            # Load existing data if available
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
            
            # Create MainAssistant instance with DataController
            print("🔧 Creating MainAssistant...")
            self.main_assistant = MainAssistant(data_controller_instance=self.data_controller)
            print("✅ MainAssistant created")
            
            print("✅ MainAssistant initialized successfully")
            print(f"📊 Current data status:")
            print(f"   - Grammar rules: {len(self.data_controller.grammar_manager.get_all_rules_name())}")
            print(f"   - Vocabulary items: {len(self.data_controller.vocab_manager.get_all_vocab_body())}")
            print(f"   - Original texts: {len(self.data_controller.text_manager.list_texts_by_title())}")
            
        except ImportError as e:
            print(f"❌ Failed to import required modules: {e}")
            import traceback
            traceback.print_exc()
            print("⚠️ MainAssistant will not be available, using fallback AI responses")
            self.main_assistant = None
            self.data_controller = None
        except Exception as e:
            print(f"❌ Failed to initialize MainAssistant: {e}")
            import traceback
            traceback.print_exc()
            print("⚠️ MainAssistant will not be available, using fallback AI responses")
            self.main_assistant = None
            self.data_controller = None
    
    def _save_data(self):
        """Save data to files"""
        if self.data_controller:
            try:
                self.data_controller.save_data(
                    grammar_path='data/grammar_rules.json',
                    vocab_path='data/vocab_expressions.json',
                    text_path='data/original_texts.json',
                    dialogue_record_path='data/dialogue_record.json',
                    dialogue_history_path='data/dialogue_history.json'
                )
                print("✅ Data saved successfully")
            except Exception as e:
                print(f"❌ Failed to save data: {e}")
    
    def _convert_to_sentence_object(self, selected_tokens, full_sentence, sentence_id, user_input):
        """Convert UI selection data to MainAssistant expected Sentence object"""
        from data_managers.data_classes import Sentence
        
        # Construct Sentence object
        sentence_object = Sentence(
            text_id=getattr(self, 'article_id', 0),
            sentence_id=sentence_id,
            sentence_body=full_sentence,
            grammar_annotations=[],  # Empty for now, will be filled by AI later
            vocab_annotations=[]     # Empty for now, will be filled by AI later
        )
        
        print(f"🔄 Converted to Sentence object:")
        print(f"   text_id: {sentence_object.text_id}")
        print(f"   sentence_id: {sentence_object.sentence_id}")
        print(f"   sentence_body: '{sentence_object.sentence_body}'")
        print(f"   selected_tokens: {selected_tokens}")
        print(f"   user_input: '{user_input}'")
        
        return sentence_object
    
    def _call_main_assistant(self, sentence_object, user_question, selected_tokens):
        """Call MainAssistant to process the user question"""
        if not self.main_assistant:
            print("⚠️ MainAssistant not available, using fallback response")
            return self._generate_fallback_response(user_question, sentence_object.sentence_body)
        
        try:
            print("🤖 Calling MainAssistant...")
            
            # Convert selected tokens to quoted string
            quoted_string = " ".join(selected_tokens) if selected_tokens else None
            
            # Call MainAssistant
            self.main_assistant.run(
                quoted_sentence=sentence_object,
                user_question=user_question,
                quoted_string=quoted_string
            )
            
            # Get the AI response from MainAssistant's session state
            if self.main_assistant and self.main_assistant.session_state:
                ai_response = self.main_assistant.session_state.current_response
                if ai_response:
                    print("✅ MainAssistant response received")
                    return ai_response
            
            # Fallback if no response found
            print("⚠️ No AI response found, using fallback")
            return self._generate_fallback_response(user_question, sentence_object.sentence_body)
            
        except Exception as e:
            print(f"❌ Error calling MainAssistant: {e}")
            print("⚠️ Using fallback response")
            return self._generate_fallback_response(user_question, sentence_object.sentence_body)
    
    def _generate_fallback_response(self, user_question, sentence_body):
        """Generate fallback response when MainAssistant is not available"""
        if sentence_body:
            return f"Fallback response: I understand you're asking about '{sentence_body[:50]}...'. This is a fallback response as the AI assistant is not fully available."
        else:
            return "Fallback response: I'm here to help with language learning. Please select some text and ask me questions about grammar, vocabulary, or meaning."
    
    def set_article(self, article_data):
        """Set article data"""
        if hasattr(article_data, 'text_title'):
            self.article_title = article_data.text_title
        else:
            self.article_title = "Test Article"
        
        if hasattr(article_data, 'text_by_sentence'):
            # Convert sentence list to text
            sentences = []
            for sentence in article_data.text_by_sentence:
                sentences.append(sentence.sentence_body)
            self.article_content = " ".join(sentences)
        else:
            self.article_content = "Article content not available."
        
        # Save article ID
        if hasattr(article_data, 'text_id'):
            self.article_id = article_data.text_id
        else:
            self.article_id = 0  # Default ID
        
        # Update UI display
        self._update_article_display()
        print(f"📖 Set article: {self.article_title} (ID: {self.article_id})")
        print(f"📝 Article content length: {len(self.article_content)} characters")
    
    def _update_article_display(self):
        """Update article display"""
        if hasattr(self, 'article_title_label'):
            self.article_title_label.text = f'Test Article: {self.article_title}'
        
        # Recreate article content (if needed)
        if hasattr(self, 'tokens'):
            self._recreate_article_content()
    
    def _tokenize_text(self, text):
        """Tokenize text into words/phrases, merge punctuation with adjacent words, and group by sentences"""
        import re
        
        # Define punctuation categories
        # Post-punctuation: should merge with previous word
        post_punctuation = r'[,\.!…?\)\]\}""'']'
        # Pre-punctuation: should merge with next word
        pre_punctuation = r'[\(\[\{"'']'
        
        # Step 1: Split text by sentences
        sentence_endings = r'[。！？\.!?\n]'
        sentences = re.split(f'({sentence_endings})', text)
        
        # Recombine sentences, preserving sentence ending punctuation
        sentence_blocks = []
        current_sentence = ""
        for i, part in enumerate(sentences):
            if re.match(sentence_endings, part):
                # This is sentence ending punctuation
                current_sentence += part
                if current_sentence.strip():
                    sentence_blocks.append(current_sentence.strip())
                current_sentence = ""
            else:
                # This is sentence content
                current_sentence += part
        
        # Handle the last sentence (if no ending punctuation)
        if current_sentence.strip():
            sentence_blocks.append(current_sentence.strip())
        
        # Step 2: Tokenize each sentence
        all_tokens = []
        sentence_boundaries = []
        token_index = 0
        
        for sentence_id, sentence in enumerate(sentence_blocks):
            # Pre-process contractions
            sentence = re.sub(r"(\w+)'(\w+)", r"\1'\2", sentence)
            
            # Tokenize with punctuation merging
            tokens = re.findall(r'\b\w+(?:[,\-\.!…?\)\]\}""'']+)?|[\w\s]*[\(\[\{"'']\w+|\w+[,\-\.!…?\)\]\}""'']+|\w+', sentence)
            
            # Post-process tokens
            processed_tokens = []
            for token in tokens:
                token = token.strip()
                if token:
                    # Clean up redundant punctuation
                    token = re.sub(r'([,\-\.!…?\)\]\}""''])\1+', r'\1', token)
                    processed_tokens.append(token)
            
            # Store sentence boundary information
            sentence_start = token_index
            sentence_end = token_index + len(processed_tokens) - 1
            sentence_boundaries.append({
                'start': sentence_start,
                'end': sentence_end,
                'sentence_id': sentence_id,
                'text': sentence
            })
            
            all_tokens.extend(processed_tokens)
            token_index += len(processed_tokens)
        
        return all_tokens, sentence_boundaries
    
    def _recreate_article_content(self):
        """重新创建文章内容，按句子分组"""
        # 清除现有内容
        if hasattr(self, 'article_content_container'):
            self.article_content_container.clear_widgets()
        
        # 重新分词
        self.tokens, self.sentence_boundaries = self._tokenize_text(self.article_content)
        self.token_widgets = []
        
        # 按句子创建UI
        for sentence_boundary in self.sentence_boundaries:
            # 创建句子容器
            sentence_container = BoxLayout(
                orientation='vertical', 
                size_hint_y=None, 
                spacing=5,
                padding=(10, 5)
            )
            sentence_container.sentence_id = sentence_boundary['sentence_id']
            
            # 创建句子内的token行
            current_line = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=5)
            line_width = 0
            
            # 获取当前句子的token范围
            start_token = sentence_boundary['start']
            end_token = sentence_boundary['end']
            
            for i in range(start_token, end_token + 1):
                if i >= len(self.tokens):
                    break
                    
                token = self.tokens[i]
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
                    token_label.token_bg = Rectangle(pos=token_label.pos, size=token_label.size)
                
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
                token_label.sentence_id = sentence_boundary['sentence_id']  # 添加句子ID
                
                self.token_widgets.append(token_label)
                
                # 检查是否需要换行
                if line_width + len(token) * 30 > 1200:
                    sentence_container.add_widget(current_line)
                    current_line = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=5)
                    line_width = 0
                
                current_line.add_widget(token_label)
                line_width += len(token) * 30 + 5
            
            # 添加最后一行
            if current_line.children:
                sentence_container.add_widget(current_line)
            
            # 计算句子容器的实际高度
            sentence_height = len(sentence_container.children) * 65  # 每行65像素
            sentence_container.height = sentence_height
            
            # 将句子容器添加到主容器
            self.article_content_container.add_widget(sentence_container)
        
        # 计算总高度
        total_height = sum(child.height for child in self.article_content_container.children) + len(self.article_content_container.children) * 10
        self.article_content_container.height = total_height
    
    def _go_back(self, instance):
        """返回主页面"""
        print("⬅️ Returning to main page")
        # Check if main screen exists
        if hasattr(self.manager, 'screens') and any(screen.name == "main" for screen in self.manager.screens):
            self.manager.current = "main"
        else:
            print("⚠️ Main screen not found, closing application")
            from kivy.app import App
            App.get_running_app().stop()
    
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
                print(f"🎯 Input box gained focus, keeping selected text: '{self.selected_text_backup}'")
            else:
                print("🎯 Input box gained focus, no text selected")
        else:  # 失去焦点
            print(f"🎯 Input box lost focus, current selected text: '{self.selected_text_backup}'")
    
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
            print(f"📝 Displaying selection: '{selected_text}'")
        else:
            # 没有任何选择
            self.selection_label.text = "No selection"
            self.selection_label.color = (0.5, 0.5, 0.5, 1)
            print("📝 Clearing selection display")
    
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
        """发送消息 - 智能提问控制逻辑"""
        message = self.chat_input.text.strip()
        if not message:
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
        
        # 🧠 智能提问控制逻辑
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
            
            # 更新上一轮上下文（用于下次follow-up）
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
        
        # 输出结构化数据
        if context_tokens:
            self._output_structured_selection_data(
                context_tokens, 
                {'text': context_sentence, 'sentence_id': context_sentence_id}, 
                user_input=message
            )
        
        # 添加用户消息到聊天界面
        if context_sentence:
            # 显示引用的句子
            quoted_text = context_sentence
            if is_follow_up:
                quoted_text = f"[Follow-up] {context_sentence}"
            self._add_chat_message("You", message, is_ai=False, quoted_text=quoted_text)
        else:
            self._add_chat_message("You", message, is_ai=False)
        
        # Convert to Sentence object and call MainAssistant
        sentence_object = self._convert_to_sentence_object(
            context_tokens, 
            context_sentence, 
            context_sentence_id, 
            message
        )
        
        # Call MainAssistant for AI response
        ai_response = self._call_main_assistant(sentence_object, message, context_tokens)
        self._add_chat_message("AI Assistant", ai_response, is_ai=True)
        
        # Save data after processing
        self._save_data()
        
        # 清空输入
        self.chat_input.text = ''

    def _show_selection_required_warning(self):
        """显示需要选择句子的警告"""
        warning_message = "⚠️ Please select a relevant sentence before asking a question"
        print(f"🚫 {warning_message}")
        
        # 在聊天界面显示警告消息
        self._add_chat_message("System", warning_message, is_ai=True)
        
        # 可选：在输入框上方显示临时提示
        if hasattr(self, 'selection_label'):
            original_text = self.selection_label.text
            self.selection_label.text = warning_message
            self.selection_label.color = (1, 0.5, 0, 1)  # 橙色警告色
            
            # 3秒后恢复原文本
            from kivy.clock import Clock
            def restore_text(dt):
                self.selection_label.text = original_text
                self.selection_label.color = (0.2, 0.2, 0.2, 1)  # 恢复原色
            
            Clock.schedule_once(restore_text, 3.0)
    
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
                return f"About the selected text '{selected_text[:30]}...' meaning, this is a great question. Let me explain..."
            elif "grammar" in user_message.lower() or "语法" in user_message:
                return f"The selected text '{selected_text[:30]}...' involves some grammar points. Let me analyze..."
            elif "pronunciation" in user_message.lower() or "发音" in user_message:
                return f"Regarding the pronunciation of '{selected_text[:30]}...', here are some key points to note..."
            else:
                return f"You asked about the selected text '{selected_text[:30]}...' question. This is a great learning point!"
        else:
            if "help" in user_message.lower() or "帮助" in user_message:
                return "I can help you learn languages! Please select any text from the article and ask me questions about grammar, vocabulary, pronunciation, or meaning."
            elif "hello" in user_message.lower() or "你好" in user_message:
                return "Hello! I am your language learning assistant. Please select text from the article, and I will answer your questions."
            else:
                return "Please select some text from the article first, then ask me related questions. I can help you understand grammar, vocabulary, pronunciation, etc."
    
    def backup_selected_text(self):
        """备份选中的文本"""
        if self.article_content_widget.selection_text:
            self.selected_text_backup = self.article_content_widget.selection_text
            self.is_text_selected = True
            print(f"📝 Backing up selected text: '{self.selected_text_backup[:30]}...'")
        elif self.selected_text_backup and self.is_text_selected:
            # 如果当前没有选择但有备份，保持备份状态
            print(f"📝 Keeping backup text: '{self.selected_text_backup[:30]}...'")
        else:
            # 没有选择也没有备份
            self.selected_text_backup = ""
            self.is_text_selected = False
            print("📝 No selected text")
    
    def clear_text_selection(self):
        """清除文本选择"""
        self.selected_text_backup = ""
        self.is_text_selected = False
        print("📝 Clearing text selection")
    
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
        if hasattr(instance, 'token_bg'):
            instance.token_bg.pos = instance.pos
            instance.token_bg.size = instance.size
    
    def _check_sentence_boundary(self, token_index):
        """检查token是否在当前选择句子的边界内"""
        if not hasattr(self, 'sentence_boundaries') or not self.sentence_boundaries:
            return True
        
        # 如果没有当前选择，允许选择
        if not self.selected_indices:
            return True
        
        # 找到当前token所属的句子
        current_sentence_id = None
        for boundary in self.sentence_boundaries:
            if boundary['start'] <= token_index <= boundary['end']:
                current_sentence_id = boundary['sentence_id']
                break
        
        if current_sentence_id is None:
            return False
        
        # 检查已选择的token是否都在同一个句子内
        for selected_index in self.selected_indices:
            selected_in_same_sentence = False
            for boundary in self.sentence_boundaries:
                if boundary['start'] <= selected_index <= boundary['end']:
                    if boundary['sentence_id'] == current_sentence_id:
                        selected_in_same_sentence = True
                    break
            if not selected_in_same_sentence:
                return False
        
        return True
    
    def _show_sentence_boundary_warning(self):
        """显示句子边界警告"""
        print("⚠️ Warning: Selection must be within the same sentence")
    
    def _on_token_touch_down(self, instance, touch):
        """token触摸按下事件"""
        print(f"�� Token touch down - '{instance.token_text}' (index: {instance.token_index}), position: {touch.pos}")
        
        # 如果触摸事件已经被其他组件抓取，不处理
        if touch.grab_current is not None:
            print(f"🔍 Touch event already grabbed: {touch.grab_current}, not processing")
            return False
        
        if instance.collide_point(*touch.pos):
            import time
            current_time = time.time()
            
            print(f"🎯 Touched token: '{instance.token_text}' (index: {instance.token_index})")
            print(f"🔍 Current drag state: {self.is_dragging}, grab state: {touch.grab_current}")
            print(f"🔍 Sentence ID: {getattr(instance, 'sentence_id', 'N/A')}")
            
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
        print(f"🔍 Token touch move - '{instance.token_text}' (index: {instance.token_index}), position: {touch.pos}")
        print(f"🔍 Grab state: {touch.grab_current}, drag state: {self.is_dragging}")
        
        # 检查触摸事件是否被当前token抓取
        if touch.grab_current != instance:
            print("🔍 Token did not grab touch event, not processing")
            return False
        
        if not self.is_dragging:
            print("�� Not in drag state, not processing")
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
        print(f"🔍 Grab state: {touch.grab_current}, drag state: {self.is_dragging}")
        
        # 检查触摸事件是否被当前token抓取
        if touch.grab_current != instance:
            print("🔍 Token did not grab touch event, not processing")
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
    
    def _output_structured_selection_data(self, selected_tokens, sentence_info, user_input=None):
        """输出结构化选择数据"""
        if not sentence_info:
            print("⚠️ Unable to find sentence information")
            return
        
        # 构造结构化数据
        structured_data = {
            'selected_tokens': selected_tokens,
            'full_sentence': sentence_info['text'],
            'sentence_id': sentence_info['sentence_id'],
            'text_id': getattr(self, 'article_id', 0)  # 文章ID，默认为0
        }
        
        # 如果有用户输入，添加到结构化数据中
        if user_input is not None:
            structured_data['user_input'] = user_input
        
        print("🎯 Structured Selection Data:")
        print(f"   selected_tokens: {structured_data['selected_tokens']}")
        print(f"   full_sentence: '{structured_data['full_sentence']}'")
        print(f"   sentence_id: {structured_data['sentence_id']}")
        print(f"   text_id: {structured_data['text_id']}")
        if user_input is not None:
            print(f"   user_input: '{structured_data['user_input']}'")
        print("📊 Complete Data Structure:")
        print(structured_data)
    
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
            
            print(f"📝 Updating selection: '{selected_text}' (indices: {sorted(self.selected_indices)})")
            
            # 获取完整句子信息并输出结构化数据
            sentence_info = self._get_full_sentence_info(self.selected_indices)
            self._output_structured_selection_data(selected_tokens, sentence_info)
            
            # 更新显示
            self._update_selection_display()
        else:
            self.selected_text_backup = ""
            self.is_text_selected = False
            self._update_selection_display()
    
    def _on_container_touch_down(self, instance, touch):
        """容器触摸事件，用于点击空白处取消选择"""
        print(f"🔍 Container touch down - position: {touch.pos}, current drag state: {self.is_dragging}")
        
        # 如果触摸事件已经被其他组件抓取，不处理
        if touch.grab_current is not None:
            print(f"🔍 Touch event already grabbed: {touch.grab_current}, not processing")
            return False
        
        # 检查是否点击了任何token
        for token_widget in self.token_widgets:
            if token_widget.collide_point(*touch.pos):
                # 点击了token，不处理（由token自己的事件处理）
                print(f"🔍 Clicked on token: '{token_widget.token_text}', not processing")
                return False
        
        # 点击了空白处，清除所有选择
        print("🎯 Clicked blank area, clearing all selections")
        print(f"🔍 State before clearing - drag: {self.is_dragging}, selected indices: {sorted(self.selected_indices)}")
        
        # 重置拖拽状态
        self.is_dragging = False
        self._clear_all_selections()
        self._update_selection_from_tokens()
        
        print(f"🔍 State after clearing - drag: {self.is_dragging}, selected indices: {sorted(self.selected_indices)}")
        
        # 标记这个触摸事件已经被处理，防止后续传播
        touch.grab(instance)
        print(f"🔍 Touch event grabbed: {touch.grab_current}")
        return True
    
    def _on_container_touch_move(self, instance, touch):
        """容器触摸移动事件"""
        print(f"🔍 Container touch move - position: {touch.pos}, grab state: {touch.grab_current}")
        
        # 如果触摸事件被容器抓取，处理移动事件
        if touch.grab_current == instance:
            print("🔍 Container has grabbed touch event, processing move")
            
            # 检查是否移动到了任何token
            for token_widget in self.token_widgets:
                if token_widget.collide_point(*touch.pos):
                    # 移动到了token，释放抓取让token处理
                    print(f"�� Moved to token: '{token_widget.token_text}', releasing grab")
                    touch.ungrab(instance)
                    return False
            
            # 继续在空白区域移动，保持抓取
            print("🔍 Continue moving in blank area, maintaining grab")
            return True
        
        print("🔍 Container has not grabbed touch event, not processing")
        return False
    
    def _on_container_touch_up(self, instance, touch):
        """容器触摸抬起事件"""
        print(f"🔍 Container touch up - position: {touch.pos}, grab state: {touch.grab_current}")
        
        # 如果触摸事件被容器抓取，释放抓取
        if touch.grab_current == instance:
            print("🔍 Container releasing touch grab")
            touch.ungrab(instance)
            return True
        
        print("🔍 Container has not grabbed touch event, not processing")
        return False
    
    def test_run(self):
        """测试运行功能 - 使用测试数据运行当前页面"""
        print("🧪 Starting test run for TextInputChatScreenTest...")
        
        # 设置测试文章数据
        test_article_data = self._create_test_article_data()
        self.set_article(test_article_data)
        
        # 添加一些测试消息
        self._add_test_messages()
        
        print("✅ Test data setup complete")
        print("📖 Article Title:", self.article_title)
        print("📝 Article content length:", len(self.article_content))
        print("💬 Number of chat messages:", len(self.chat_history))
    
    def _create_test_article_data(self):
        """创建测试文章数据"""
        class TestArticleData:
            def __init__(self):
                self.text_id = 3  # 设置文章ID
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
                print(f"📝 Simulating text selection: '{scenario['selected_text']}'")
            
            # 添加用户消息
            self._add_chat_message("You", scenario['user_message'], is_ai=False, quoted_text=scenario['selected_text'] if scenario['selected_text'] else None)
            
            # 添加AI回复
            self._add_chat_message("Test AI Assistant", scenario['ai_response'], is_ai=True)
            
            # 清除选择状态
            if scenario['selected_text']:
                self._on_text_selection_change(None, "")
        
        print(f"✅ Added {len(test_scenarios)} test conversation scenarios") 