from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp

class VocabDetailScreen(Screen):
    """词汇详情页面 - 显示词汇的详细信息"""
    
    # 数据属性
    vocab_name = StringProperty("")
    vocab_explanation = StringProperty("")
    example_sentence = StringProperty("")
    example_explanation = StringProperty("")
    
    def __init__(self, vocab_data=None, **kwargs):
        super().__init__(**kwargs)
        self.vocab_data = vocab_data or {}
        self.setup_ui()
        self.load_vocab_data()

    def setup_ui(self):
        """设置UI布局"""
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=0, spacing=0)
        
        # 内容区外层加padding和圆角白底
        content_outer = BoxLayout(orientation='vertical', padding=10, size_hint_y=1)
        with content_outer.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(pos=content_outer.pos, size=content_outer.size, radius=[20])
        content_outer.bind(pos=self._update_bg, size=self._update_bg)

        # 顶部返回按钮
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, padding=(5, 0, 0, 0))
        back_btn = Button(
            text='<', 
            size_hint_x=None, 
            width=40, 
            background_color=(0,0,0,0), 
            color=(0,0,0,1), 
            font_size=20
        )
        back_btn.bind(on_press=self.go_back)
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Widget())
        content_outer.add_widget(top_bar)

        # 滚动内容区
        scroll = ScrollView(size_hint_y=1)
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=20, padding=(10,0,10,20))
        content_box.bind(minimum_height=lambda inst, val: setattr(content_box, 'height', val))

        # 词汇标题
        self.vocab_label = Label(
            text='[b]vocab1[/b]', 
            markup=True, 
            font_size=32, 
            color=(0,0,0,1), 
            size_hint_y=None, 
            height=50, 
            halign='left', 
            valign='middle',
            text_size=(None, None)
        )
        self.vocab_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(self.vocab_label)
        
        # 词汇解释
        self.explanation_label = Label(
            text='a brief explanation ...', 
            font_size=18, 
            color=(0,0,0,1), 
            size_hint_y=None, 
            height=60, 
            halign='left', 
            valign='top',
            text_size=(None, None)
        )
        self.explanation_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(self.explanation_label)
        
        # Example区块标题
        example_title = Label(
            text='[b]Example[/b]', 
            markup=True, 
            font_size=20, 
            color=(0,0,0,1), 
            size_hint_y=None, 
            height=30, 
            halign='left', 
            valign='middle'
        )
        example_title.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(example_title)
        
        # 示例句子
        self.sentence_label = Label(
            text='An example sentence', 
            font_size=16, 
            color=(0,0,0,1), 
            size_hint_y=None, 
            height=40, 
            halign='left', 
            valign='top',
            text_size=(None, None)
        )
        self.sentence_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(self.sentence_label)
        
        # 示例解释
        self.example_explanation_label = Label(
            text='a brief explanation of example...', 
            font_size=16, 
            color=(0,0,0,1), 
            size_hint_y=None, 
            height=40, 
            halign='left', 
            valign='top',
            text_size=(None, None)
        )
        self.example_explanation_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(self.example_explanation_label)
        
        scroll.add_widget(content_box)
        content_outer.add_widget(scroll)
        main_layout.add_widget(content_outer)

        # 底部导航栏
        bottom_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=0)
        
        # Read按钮
        read_btn = Button(
            text='read',
            size_hint_x=0.5,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=18
        )
        read_btn.bind(on_press=self.go_to_read)
        bottom_bar.add_widget(read_btn)
        
        # Learn按钮
        learn_btn = Button(
            text='learn',
            size_hint_x=0.5,
            background_color=(0.2, 0.8, 0.4, 1),
            color=(1, 1, 1, 1),
            font_size=18
        )
        learn_btn.bind(on_press=self.go_to_learn)
        bottom_bar.add_widget(learn_btn)
        
        main_layout.add_widget(bottom_bar)
        self.add_widget(main_layout)

    def _update_bg(self, *args):
        """更新背景"""
        self.bg_rect.pos = self.children[0].pos
        self.bg_rect.size = self.children[0].size
    
    def _adjust_label_height(self, label):
        """动态调整标签高度"""
        try:
            from kivy.core.text import Label as CoreLabel
            # 创建临时标签来计算文本高度
            temp_label = CoreLabel(
                text=label.text,
                font_size=label.font_size,
                font_name=label.font_name,
                width=label.width if label.width else 300
            )
            temp_label.refresh()
            
            # 计算所需高度，添加一些padding
            text_height = temp_label.height + 20
            min_height = 40  # 最小高度
            
            # 设置标签高度
            label.height = max(text_height, min_height)
            
        except Exception as e:
            print(f"⚠️ Could not adjust label height: {e}")
            # 如果计算失败，使用默认高度
            label.height = 60

    def load_vocab_data(self):
        """加载词汇数据"""
        if not self.vocab_data:
            return
            
        # 更新词汇名称
        vocab_body = self.vocab_data.get('vocab_body', 'Unknown')
        self.vocab_label.text = f'[b]{vocab_body}[/b]'
        
        # 更新词汇解释
        explanation = self.vocab_data.get('explanation', 'No explanation available')
        
        # 处理explanation格式 - 可能是字符串化的字典
        if explanation.startswith('{') and explanation.endswith('}'):
            try:
                import json
                import ast
                # 尝试解析为字典
                if "'" in explanation:
                    # 使用ast.literal_eval处理单引号字典
                    explanation_dict = ast.literal_eval(explanation)
                else:
                    # 使用json.loads处理双引号字典
                    explanation_dict = json.loads(explanation)
                
                # 提取explanation字段
                if isinstance(explanation_dict, dict) and 'explanation' in explanation_dict:
                    explanation = explanation_dict['explanation']
            except Exception as e:
                print(f"⚠️ Could not parse explanation: {e}")
                # 如果解析失败，使用原始文本
        
        self.explanation_label.text = explanation
        # 动态调整高度
        self._adjust_label_height(self.explanation_label)
        
        # 获取示例数据
        examples = self.vocab_data.get('examples', [])
        if examples:
            example = examples[0]
            
            # 获取示例句子
            try:
                from data_managers.original_text_manager import OriginalTextManager
                text_manager = OriginalTextManager()
                text_manager.load_from_file("data/original_texts.json")
                sentence = text_manager.get_sentence_by_id(example.get('text_id'), example.get('sentence_id'))
                if sentence:
                    self.sentence_label.text = sentence.sentence_body
            except Exception as e:
                print(f"⚠️ Could not load example sentence: {e}")
                self.sentence_label.text = "Example sentence not available"
            
            # 获取示例解释
            context_explanation = example.get('context_explanation', '')
            if context_explanation:
                # 处理JSON格式的解释
                if context_explanation.startswith('```json'):
                    try:
                        import json
                        # 提取JSON部分
                        json_start = context_explanation.find('{')
                        json_end = context_explanation.rfind('}') + 1
                        if json_start != -1 and json_end != 0:
                            json_str = context_explanation[json_start:json_end]
                            json_data = json.loads(json_str)
                            explanation_text = json_data.get('explanation', context_explanation)
                        else:
                            explanation_text = context_explanation
                    except:
                        explanation_text = context_explanation
                else:
                    explanation_text = context_explanation
                
                self.example_explanation_label.text = explanation_text
                # 动态调整高度
                self._adjust_label_height(self.example_explanation_label)
            else:
                self.example_explanation_label.text = "No explanation available"
                self._adjust_label_height(self.example_explanation_label)

    def go_back(self, instance):
        """返回上一页"""
        if self.manager:
            # 尝试返回到learn_screen，如果不存在则返回到test_screen
            if 'learn_screen' in self.manager.screen_names:
                self.manager.current = 'learn_screen'
            elif 'test_screen' in self.manager.screen_names:
                self.manager.current = 'test_screen'
            else:
                # 如果都没有，返回到第一个屏幕
                self.manager.current = self.manager.screen_names[0]

    def go_to_read(self, instance):
        """跳转到阅读页面"""
        if self.manager:
            if 'main' in self.manager.screen_names:
                self.manager.current = 'main'
            else:
                self.manager.current = self.manager.screen_names[0]

    def go_to_learn(self, instance):
        """跳转到学习页面"""
        if self.manager:
            if 'learn_screen' in self.manager.screen_names:
                self.manager.current = 'learn_screen'
            elif 'test_screen' in self.manager.screen_names:
                self.manager.current = 'test_screen'
            else:
                self.manager.current = self.manager.screen_names[0] 