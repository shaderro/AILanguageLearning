"""
文本输入聊天屏幕模块
处理文章阅读和AI聊天的UI界面
整合了MainAssistant和智能提问功能
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
import re

class TextInputChatScreen(Screen):
    """文本输入聊天屏幕 - 整合MainAssistant功能"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history = []
        self.selected_text_backup = ""
        self.is_text_selected = False
        self.selection_start = 0
        self.selection_end = 0
        
        # 新增：MainAssistant集成相关
        self.main_assistant = None
        self.data_controller = None
        self.article_id = 0
        
        # 新增：智能提问逻辑相关
        self.previous_context_tokens = []
        self.previous_context_sentence = ""
        self.previous_context_sentence_id = -1
        self.last_used_tokens = []
        self.last_used_sentence_info = None
        
        # 新增：文本处理相关
        self.tokens = []
        self.selected_indices = set()
        self.selection_start_index = -1
        self.selection_end_index = -1
        self.is_dragging = False
        self.sentences = []
        self.sentence_containers = []
        
        # 文章数据
        self.article_title = "Article Title"
        self.article_content = """The Internet and Language Learning

The internet has revolutionized the way we learn languages. With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.

Online language learning platforms offer a variety of features that traditional classroom settings cannot provide. These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.

One of the most significant advantages of internet-based language learning is the availability of authentic materials. Learners can access real news articles, videos, podcasts, and social media content in their target language.

Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs. Students can connect with peers from different countries, practice conversation skills, and share cultural insights."""
        
        # 初始化MainAssistant
        self._initialize_main_assistant()
        
        self._setup_ui()
        self._bind_events()
    
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
            import traceback
            traceback.print_exc()
            return self._generate_fallback_response(user_question, sentence_object.sentence_body)
    
    def _generate_fallback_response(self, user_question, sentence_body):
        """Generate fallback response when MainAssistant is not available"""
        return f"I understand you're asking about: '{user_question}' regarding the sentence: '{sentence_body}'. Please try again later when the AI assistant is available."
    
    def set_article(self, article_data):
        """设置文章数据"""
        if hasattr(article_data, 'text_title'):
            self.article_title = article_data.text_title
        else:
            self.article_title = "Article Title"
        
        if hasattr(article_data, 'text_by_sentence'):
            # 将句子列表转换为文本
            sentences = []
            for sentence in article_data.text_by_sentence:
                sentences.append(sentence.sentence_body)
            self.article_content = " ".join(sentences)
        else:
            self.article_content = "Article content not available."
        
        # 设置文章ID
        if hasattr(article_data, 'text_id'):
            self.article_id = article_data.text_id
        
        # 更新UI显示
        self._update_article_display()
        print(f"📖 设置文章: {self.article_title}")
        print(f"📝 文章内容长度: {len(self.article_content)} 字符")
    
    def _update_article_display(self):
        """更新文章显示"""
        if hasattr(self, 'article_title_label'):
            self.article_title_label.text = f'Article: {self.article_title}'
        
        if hasattr(self, 'article_content_widget'):
            self.article_content_widget.text = self.article_content
        
        # 新增：重新创建文章内容（支持token选择）
        self._recreate_article_content()
    
    def _tokenize_text(self, text):
        """Tokenize text with punctuation merging"""
        # 使用正则表达式分割文本，保持标点符号与单词的关联
        # 匹配单词、标点符号、空格等
        pattern = r'[\w\']+|[^\w\s]|\s+'
        raw_tokens = re.findall(pattern, text)
        
        # 处理标点符号合并
        processed_tokens = []
        i = 0
        while i < len(raw_tokens):
            token = raw_tokens[i]
            
            # 跳过纯空格
            if token.isspace():
                i += 1
                continue
            
            # 处理标点符号
            if token in ',.!?…"\'()':
                # 如果是左括号或前引号，与下一个词合并
                if token in '("\'':
                    if i + 1 < len(raw_tokens) and not raw_tokens[i + 1].isspace():
                        combined = token + raw_tokens[i + 1]
                        processed_tokens.append(combined)
                        i += 2
                        continue
                    else:
                        processed_tokens.append(token)
                        i += 1
                        continue
                
                # 如果是右括号或后引号，与前一个词合并
                elif token in ')"\'':
                    if processed_tokens:
                        processed_tokens[-1] += token
                    else:
                        processed_tokens.append(token)
                    i += 1
                    continue
                
                # 其他标点符号与前一个词合并
                else:
                    if processed_tokens:
                        processed_tokens[-1] += token
                    else:
                        processed_tokens.append(token)
                    i += 1
                    continue
            
            # 普通单词直接添加
            processed_tokens.append(token)
            i += 1
        
        return [token for token in processed_tokens if token.strip()]
    
    def _recreate_article_content(self):
        """重新创建文章内容，支持句子分割和token选择"""
        if not hasattr(self, 'article_content_container'):
            return
        
        # 清空现有内容
        self.article_content_container.clear_widgets()
        self.tokens = []
        self.sentences = []
        self.sentence_containers = []
        
        # 分割句子
        sentence_pattern = r'[^.!?。！？\n]+[.!?。！？\n]+'
        sentence_matches = re.finditer(sentence_pattern, self.article_content, re.MULTILINE)
        
        sentence_id = 0
        for match in sentence_matches:
            sentence_text = match.group().strip()
            if not sentence_text:
                continue
            
            # 为每个句子创建容器
            sentence_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=2)
            sentence_container.sentence_id = sentence_id
            
            # Tokenize句子
            sentence_tokens = self._tokenize_text(sentence_text)
            self.sentences.append({
                'text': sentence_text,
                'sentence_id': sentence_id,
                'tokens': sentence_tokens
            })
            
            # 为每个token创建标签
            for token in sentence_tokens:
                token_label = Label(
                    text=token,
                    size_hint_x=None,
                    width=len(token) * 10 + 10,
                    size_hint_y=None,
                    height=25,
                    color=(0, 0, 0, 1),
                    halign='left',
                    valign='middle'
                )
                
                # 为每个token创建独立的背景
                token_label.token_bg = Rectangle(pos=token_label.pos, size=token_label.size)
                token_label.canvas.before.add(Color(0.9, 0.9, 0.9, 1))
                token_label.canvas.before.add(token_label.token_bg)
                
                # 绑定触摸事件
                token_label.bind(
                    pos=self._update_token_bg,
                    size=self._update_token_bg,
                    on_touch_down=self._on_token_touch_down,
                    on_touch_move=self._on_token_touch_move,
                    on_touch_up=self._on_token_touch_up
                )
                
                sentence_container.add_widget(token_label)
                self.tokens.append(token)
            
            self.article_content_container.add_widget(sentence_container)
            self.sentence_containers.append(sentence_container)
            sentence_id += 1
        
        # 绑定容器高度自动调整
        self.article_content_container.bind(minimum_height=self.article_content_container.setter('height'))
    
    def _update_token_bg(self, instance, value):
        """Update token background position and size"""
        if hasattr(instance, 'token_bg'):
            instance.token_bg.pos = instance.pos
            instance.token_bg.size = instance.size
    
    def _on_token_touch_down(self, instance, touch):
        """Handle token touch down event"""
        if not instance.collide_point(*touch.pos):
            return False
        
        if touch.grab_current is not None:
            return False
        
        print(f"🎯 Token touch down: {instance.text}")
        
        # 找到token的索引
        token_index = -1
        for i, token in enumerate(self.tokens):
            if token == instance.text:
                token_index = i
                break
        
        if token_index == -1:
            return False
        
        # 检查句子边界
        if not self._check_sentence_boundary(token_index):
            self._show_sentence_boundary_warning()
            return False
        
        # 开始选择
        self.is_dragging = True
        self.selection_start_index = token_index
        self.selection_end_index = token_index
        self.selected_indices = {token_index}
        
        # 高亮选中的token
        self._highlight_token(instance, True)
        
        # 抓取触摸事件
        touch.grab(instance)
        return True
    
    def _on_token_touch_move(self, instance, touch):
        """Handle token touch move event"""
        if not self.is_dragging or touch.grab_current != instance:
            return False
        
        # 找到当前触摸位置的token
        current_token_index = -1
        for i, token in enumerate(self.tokens):
            if token == instance.text:
                current_token_index = i
                break
        
        if current_token_index == -1:
            return False
        
        # 更新选择范围
        start = min(self.selection_start_index, current_token_index)
        end = max(self.selection_start_index, current_token_index)
        
        # 检查句子边界
        if not self._check_sentence_boundary(start, end):
            self._show_sentence_boundary_warning()
            return False
        
        # 更新选择
        self.selection_end_index = current_token_index
        self.selected_indices = set(range(start, end + 1))
        
        # 更新高亮显示
        self._highlight_selection_range()
        
        return True
    
    def _on_token_touch_up(self, instance, touch):
        """Handle token touch up event"""
        if not self.is_dragging or touch.grab_current != instance:
            return False
        
        print(f"🎯 Token selection completed: {len(self.selected_indices)} tokens")
        
        # 结束拖拽
        self.is_dragging = False
        touch.ungrab(instance)
        
        # 更新选择状态
        self.is_text_selected = len(self.selected_indices) > 0
        if self.is_text_selected:
            selected_text = " ".join([self.tokens[i] for i in sorted(self.selected_indices)])
            print(f"📝 Selected text: '{selected_text}'")
        
        return True
    
    def _check_sentence_boundary(self, start_index, end_index=None):
        """Check if selection is within sentence boundary"""
        if end_index is None:
            end_index = start_index
        
        # 找到start_index和end_index所在的句子
        start_sentence_id = -1
        end_sentence_id = -1
        
        current_index = 0
        for sentence in self.sentences:
            sentence_length = len(sentence['tokens'])
            if start_index >= current_index and start_index < current_index + sentence_length:
                start_sentence_id = sentence['sentence_id']
            if end_index >= current_index and end_index < current_index + sentence_length:
                end_sentence_id = sentence['sentence_id']
            current_index += sentence_length
        
        # 检查是否在同一句子内
        return start_sentence_id == end_sentence_id and start_sentence_id != -1
    
    def _show_sentence_boundary_warning(self):
        """Show sentence boundary warning"""
        print("⚠️ Selection must be within a single sentence")
    
    def _highlight_token(self, token_widget, is_selected):
        """Highlight or unhighlight a token"""
        if is_selected:
            token_widget.canvas.before.clear()
            token_widget.canvas.before.add(Color(0.3, 0.7, 1.0, 1))
            token_widget.canvas.before.add(token_widget.token_bg)
        else:
            token_widget.canvas.before.clear()
            token_widget.canvas.before.add(Color(0.9, 0.9, 0.9, 1))
            token_widget.canvas.before.add(token_widget.token_bg)
    
    def _highlight_selection_range(self):
        """Highlight all tokens in the current selection range"""
        # 清除所有高亮
        for sentence_container in self.sentence_containers:
            for child in sentence_container.children:
                if hasattr(child, 'text'):
                    self._highlight_token(child, False)
        
        # 高亮选中的tokens
        current_index = 0
        for sentence in self.sentences:
            sentence_length = len(sentence['tokens'])
            for i in range(sentence_length):
                if current_index + i in self.selected_indices:
                    # 找到对应的widget并高亮
                    sentence_container = self.sentence_containers[sentence['sentence_id']]
                    if i < len(sentence_container.children):
                        token_widget = sentence_container.children[-(i + 1)]  # 反向索引
                        self._highlight_token(token_widget, True)
            current_index += sentence_length
    
    def _get_full_sentence_info(self, token_indices):
        """Get full sentence information for selected tokens"""
        if not token_indices:
            return None
        
        # 找到第一个token所在的句子
        current_index = 0
        for sentence in self.sentences:
            sentence_length = len(sentence['tokens'])
            if any(index >= current_index and index < current_index + sentence_length for index in token_indices):
                return {
                    'text': sentence['text'],
                    'sentence_id': sentence['sentence_id']
                }
            current_index += sentence_length
        
        return None
    
    def _output_structured_selection_data(self, selected_tokens, sentence_info, user_input=None):
        """Output structured selection data"""
        if not sentence_info:
            print("⚠️ Unable to find sentence information")
            return
        
        # Construct structured data
        structured_data = {
            'selected_tokens': selected_tokens,
            'full_sentence': sentence_info['text'],
            'sentence_id': sentence_info['sentence_id'],
            'text_id': getattr(self, 'article_id', 0)  # Article ID, default to 0
        }
        
        # Add user input if provided
        if user_input is not None:
            structured_data['user_input'] = user_input
        
        print("🎯 Structured Selection Data:")
        print(f"   selected_tokens: {structured_data['selected_tokens']}")
        print(f"   full_sentence: '{structured_data['full_sentence']}'")
        print(f"   sentence_id: {structured_data['sentence_id']}")
        print(f"   text_id: {structured_data['text_id']}")
        if 'user_input' in structured_data:
            print(f"   user_input: '{structured_data['user_input']}'")
        print("📊 Complete Data Structure:")
        print(structured_data)
    
    def _show_selection_required_warning(self):
        """Show warning when selection is required"""
        warning_message = "⚠️ Please select a relevant sentence before asking a question"
        print(f"🚫 {warning_message}")
        
        # Add warning message to chat
        self._add_chat_message("System", warning_message, is_ai=False)
    
    def _go_back(self, instance):
        """Return to main page"""
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
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        
        # 返回按钮
        back_button = Button(
            text="← Back",
            size_hint_x=None,
            width=80,
            size_hint_y=None,
            height=35,
            background_color=(0.3, 0.7, 1.0, 1)
        )
        back_button.bind(on_press=self._go_back)
        top_bar.add_widget(back_button)
        
        # 文章标题
        self.article_title_label = Label(
            text=f'Article: {self.article_title}',
            size_hint_x=1,
            size_hint_y=None,
            height=35,
            color=(0, 0, 0, 1),
            halign='left',
            valign='middle'
        )
        top_bar.add_widget(self.article_title_label)
        
        return top_bar
    
    def _create_article_title(self):
        """创建文章标题"""
        title_label = Label(
            text=f'Article: {self.article_title}',
            size_hint_y=None,
            height=40,
            color=(0, 0, 0, 1),
            halign='left',
            valign='middle'
        )
        return title_label
    
    def _create_article_content(self):
        """创建文章内容区域"""
        # 创建滚动视图
        self.article_content_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True
        )
        
        # 创建文章内容容器
        self.article_content_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5,
            padding=10
        )
        
        # 绑定容器高度自动调整
        self.article_content_container.bind(minimum_height=self.article_content_container.setter('height'))
        
        # 初始显示文章内容
        self.article_content_widget = Label(
            text=self.article_content,
            size_hint_y=None,
            height=200,
            color=(0, 0, 0, 1),
            halign='left',
            valign='top',
            text_size=(None, None)
        )
        self.article_content_container.add_widget(self.article_content_widget)
        
        self.article_content_scroll.add_widget(self.article_content_container)
        return self.article_content_scroll
    
    def _create_selection_label(self):
        """创建选择状态标签"""
        self.selection_label = Label(
            text="No text selected",
            size_hint_y=None,
            height=30,
            color=(0.5, 0.5, 0.5, 1),
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
        chat_scroll = self._create_chat_scroll_area()
        chat_panel.add_widget(chat_scroll)
        
        # 输入区域
        input_layout = self._create_input_layout()
        chat_panel.add_widget(input_layout)
        
        return chat_panel
    
    def _create_chat_title(self):
        """创建聊天标题"""
        title_label = Label(
            text="AI Chat Assistant",
            size_hint_y=None,
            height=30,
            color=(0, 0, 0, 1),
            halign='left',
            valign='middle'
        )
        return title_label
    
    def _create_chat_scroll_area(self):
        """创建聊天滚动区域"""
        # 聊天滚动视图
        self.chat_scroll_view = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True
        )
        
        # 聊天消息容器
        self.chat_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5,
            padding=10
        )
        self.chat_container.bind(minimum_height=self.chat_container.setter('height'))
        
        self.chat_scroll_view.add_widget(self.chat_container)
        return self.chat_scroll_view
    
    def _create_input_layout(self):
        """创建输入布局"""
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        
        # 聊天输入框
        self.chat_input = TextInput(
            hint_text="Type your question here...",
            size_hint_x=0.8,
            size_hint_y=None,
            height=35,
            multiline=False
        )
        input_layout.add_widget(self.chat_input)
        
        # 发送按钮
        send_button = Button(
            text="Send",
            size_hint_x=0.2,
            size_hint_y=None,
            height=35,
            background_color=(0.3, 0.7, 1.0, 1)
        )
        send_button.bind(on_press=self._on_send_message)
        input_layout.add_widget(send_button)
        
        return input_layout
    
    def _bind_events(self):
        """绑定事件"""
        # 绑定输入框事件
        self.chat_input.bind(
            on_text_validate=self._on_send_message,
            on_text=self._block_input,
            focus=self._on_chat_input_focus
        )
        
        # 绑定选择变化事件
        Clock.schedule_interval(self._update_selection_display, 0.1)
    
    def _block_input(self, text, from_undo):
        """阻止输入框的撤销操作"""
        if from_undo:
            return False
        return True
    
    def _on_chat_input_focus(self, instance, value):
        """处理输入框焦点事件"""
        if value:
            print("📝 Chat input focused")
        else:
            print("📝 Chat input lost focus")
    
    def _on_text_selection_change(self, instance, value):
        """处理文本选择变化"""
        if hasattr(instance, 'selection_text'):
            selected_text = instance.selection_text
            print(f"📝 Text selection changed: '{selected_text}'")
    
    def _update_selection_display(self, dt=None):
        """更新选择显示"""
        if self.is_text_selected and self.selected_indices:
            selected_text = " ".join([self.tokens[i] for i in sorted(self.selected_indices)])
            self.selection_label.text = f"Selected: {selected_text}"
        else:
            self.selection_label.text = "No text selected"
    
    def _get_selected_text(self):
        """获取选中的文本"""
        if self.is_text_selected and self.selected_indices:
            return " ".join([self.tokens[i] for i in sorted(self.selected_indices)])
        return ""
    
    def _keep_text_highlighted(self):
        """保持文本高亮"""
        if self.is_text_selected:
            print("🔍 Keeping text highlighted")
    
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
        
        # Convert to Sentence object and call MainAssistant
        sentence_object = self._convert_to_sentence_object(
            context_tokens, 
            context_sentence, 
            context_sentence_id, 
            message
        )
        
        # Add user message to chat history
        if context_sentence:
            # 显示引用的句子
            quoted_text = context_sentence
            if is_follow_up:
                quoted_text = f"[Follow-up] {context_sentence}"
            self._add_chat_message("You", message, is_ai=False, quoted_text=quoted_text)
        else:
            self._add_chat_message("You", message, is_ai=False)
        
        # Call MainAssistant for AI response
        ai_response = self._call_main_assistant(sentence_object, message, context_tokens)
        self._add_chat_message("AI Assistant", ai_response, is_ai=True)
        
        # Save data after processing
        self._save_data()
        
        # 清空输入
        self.chat_input.text = ''
    
    def _add_chat_message(self, sender, message, is_ai=False, quoted_text=None):
        """添加聊天消息"""
        # 创建消息容器
        message_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        message_container.bind(minimum_height=message_container.setter('height'))
        
        # 发送者标签
        sender_color = (0.3, 0.7, 1.0, 1) if is_ai else (0.2, 0.8, 0.2, 1)
        sender_label = Label(
            text=sender,
            size_hint_y=None,
            height=20,
            color=sender_color,
            halign='left',
            valign='middle'
        )
        message_container.add_widget(sender_label)
        
        # 引用文本（如果有）
        if quoted_text:
            quoted_label = Label(
                text=f"Quote: {quoted_text}",
                size_hint_y=None,
                height=30,
                color=(0.6, 0.6, 0.6, 1),
                halign='left',
                valign='middle',
                text_size=(None, None)
            )
            message_container.add_widget(quoted_label)
        
        # 消息内容
        message_label = Label(
            text=message,
            size_hint_y=None,
            height=40,
            color=(0, 0, 0, 1),
            halign='left',
            valign='top',
            text_size=(None, None)
        )
        message_label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1] + 10))
        message_container.add_widget(message_label)
        
        # 添加到聊天容器
        self.chat_container.add_widget(message_container)
        
        # 滚动到底部
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll_view, 'scroll_y', 0), 0.1)
        
        # 保存到聊天历史
        self.chat_history.append({
            'sender': sender,
            'message': message,
            'is_ai': is_ai,
            'quoted_text': quoted_text
        })
        
        print(f"💬 Added chat message: {sender} - {message[:50]}...")
    
    def _generate_ai_response(self, user_message, selected_text):
        """生成AI回复（备用方法）"""
        if selected_text:
            return f"I understand you're asking about '{user_message}' regarding the text: '{selected_text}'. This is a fallback response."
        else:
            return f"I understand your question: '{user_message}'. This is a fallback response."
    
    def backup_selected_text(self):
        """备份选中的文本"""
        if self.is_text_selected:
            self.selected_text_backup = self._get_selected_text()
            print(f"💾 Backed up selected text: '{self.selected_text_backup}'")
    
    def clear_text_selection(self):
        """清除文本选择"""
        self.is_text_selected = False
        self.selected_indices.clear()
        self._update_selection_display()
        print("🧹 Cleared text selection")
    
    def _update_article_title_bg(self, *args):
        """更新文章标题背景"""
        pass
    
    def _update_chat_title_bg(self, *args):
        """更新聊天标题背景"""
        pass
    
    def _update_selection_label_bg(self, *args):
        """更新选择标签背景"""
        pass
    
    def _update_chat_scroll_bg(self, *args):
        """更新聊天滚动背景"""
        pass
    
    def _update_chat_container_bg(self, *args):
        """更新聊天容器背景"""
        pass 