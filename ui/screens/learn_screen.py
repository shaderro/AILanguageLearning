"""
Learn screen
Display grammar rules and vocabulary expression cards
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

from ui.viewmodels.learn_screen_viewmodel import LearnScreenViewModel
from ui.components.learn_cards import (
    GrammarRuleCard, VocabExpressionCard, 
    CategoryFilterButton, SearchBox
)
from ui.components.buttons import TabButton, BottomTabBar
from ui.utils.font_utils import FontUtils


class LearnScreen(Screen):
    """Learn screen"""
    
    # ViewModel reference
    viewmodel: LearnScreenViewModel = ObjectProperty(None)
    
    def __init__(self, data_binding_service=None, **kwargs):
        super().__init__(**kwargs)
        self.name = "learn_screen"
        
        # Set white background
        self._setup_background()
        
        # Initialize ViewModel
        self.viewmodel = LearnScreenViewModel(data_binding_service=data_binding_service)
        
        # Build UI
        self._build_ui()
        
        # Bind data changes
        self._bind_data()
        
        # Initialize data
        Clock.schedule_once(self._initialize_data, 0.1)
    
    def _setup_background(self):
        """Setup white background"""
        with self.canvas.before:
            Color(1, 1, 1, 1)  # White background
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
    
    def _update_bg(self, *args):
        """Update background"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def _build_ui(self):
        """Build UI interface"""
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Title
        title = FontUtils.create_label_with_chinese_support(
            text="[b][color=000000]Learning Center[/color][/b]",
            markup=True, font_size=48, size_hint_y=None, height=80,
            halign='center', valign='middle'
        )
        main_layout.add_widget(title)
        
        # Search box
        self.search_box = SearchBox(on_text_change=self._on_search_text_change)
        main_layout.add_widget(self.search_box)
        
        # Category filter buttons
        filter_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=60)
        
        self.grammar_button = CategoryFilterButton(
            "Grammar", "grammar", True, self._on_category_filter_change
        )
        self.vocab_button = CategoryFilterButton(
            "Vocabulary", "vocab", False, self._on_category_filter_change
        )
        
        filter_layout.add_widget(self.grammar_button)
        filter_layout.add_widget(self.vocab_button)
        main_layout.add_widget(filter_layout)
        
        # Statistics
        stats_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        self.grammar_stats = FontUtils.create_label_with_chinese_support(
            text="[color=000000]Grammar Rules: 0[/color]",
            markup=True, font_size=24, halign='left', valign='middle'
        )
        self.vocab_stats = FontUtils.create_label_with_chinese_support(
            text="[color=000000]Vocabulary: 0[/color]",
            markup=True, font_size=24, halign='right', valign='middle'
        )
        
        stats_layout.add_widget(self.grammar_stats)
        stats_layout.add_widget(self.vocab_stats)
        main_layout.add_widget(stats_layout)
        
        # Content area
        self.content_layout = BoxLayout(orientation='vertical', spacing=15)
        
        # Grammar rules section
        self.grammar_section = self._build_grammar_section()
        self.content_layout.add_widget(self.grammar_section)
        
        # Vocabulary expressions section
        self.vocab_section = self._build_vocab_section()
        self.content_layout.add_widget(self.vocab_section)
        
        # Scroll view
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(self.content_layout)
        main_layout.add_widget(scroll_view)
        
        # Bottom tab bar
        self._setup_bottom_tab_bar(main_layout)
        
        self.add_widget(main_layout)
    
    def _setup_bottom_tab_bar(self, parent_layout):
        """Setup bottom tab bar with Read and Learn tabs"""
        # Use unified BottomTabBar component
        self.tab_bar = BottomTabBar(
            read_callback=self._on_read_tab_press,
            learn_callback=self._on_learn_tab_press,
            active_tab="learn"
        )
        parent_layout.add_widget(self.tab_bar)
    
    def _build_grammar_section(self) -> BoxLayout:
        """Build grammar rules section"""
        section = BoxLayout(orientation='vertical', spacing=10)
        
        # Title
        grammar_title = FontUtils.create_label_with_chinese_support(
            text="[b][color=000000]Grammar Rules[/color][/b]",
            markup=True, font_size=36, size_hint_y=None, height=60,
            halign='left', valign='middle'
        )
        section.add_widget(grammar_title)
        
        # Grammar cards container
        self.grammar_container = GridLayout(
            cols=1, spacing=15, size_hint_y=None
        )
        self.grammar_container.bind(minimum_height=self.grammar_container.setter('height'))
        
        # Grammar scroll view - 使用自适应高度
        grammar_scroll = ScrollView(size_hint=(1, 1))
        grammar_scroll.add_widget(self.grammar_container)
        section.add_widget(grammar_scroll)
        
        return section
    
    def _build_vocab_section(self) -> BoxLayout:
        """Build vocabulary expressions section"""
        section = BoxLayout(orientation='vertical', spacing=10)
        
        # Title
        vocab_title = FontUtils.create_label_with_chinese_support(
            text="[b][color=000000]Vocabulary Expressions[/color][/b]",
            markup=True, font_size=36, size_hint_y=None, height=60,
            halign='left', valign='middle'
        )
        section.add_widget(vocab_title)
        
        # Vocabulary cards container
        self.vocab_container = GridLayout(
            cols=1, spacing=15, size_hint_y=None
        )
        self.vocab_container.bind(minimum_height=self.vocab_container.setter('height'))
        
        # Vocabulary scroll view - 使用自适应高度
        vocab_scroll = ScrollView(size_hint=(1, 1))
        vocab_scroll.add_widget(self.vocab_container)
        section.add_widget(vocab_scroll)
        
        return section
    
    def _bind_data(self):
        """Bind data changes"""
        # Bind grammar data
        self.viewmodel.bind(grammar_rules=self._on_grammar_rules_changed)
        self.viewmodel.bind(grammar_loading=self._on_grammar_loading_changed)
        self.viewmodel.bind(grammar_error=self._on_grammar_error_changed)
        
        # Bind vocabulary data
        self.viewmodel.bind(vocab_expressions=self._on_vocab_expressions_changed)
        self.viewmodel.bind(vocab_loading=self._on_vocab_loading_changed)
        self.viewmodel.bind(vocab_error=self._on_vocab_error_changed)
        
        # Bind statistics
        self.viewmodel.bind(total_grammar_rules=self._on_total_grammar_rules_changed)
        self.viewmodel.bind(total_vocab_expressions=self._on_total_vocab_expressions_changed)
    
    def _initialize_data(self, dt):
        """Initialize data"""
        print("🔧 LearnScreen: 开始初始化数据...")
        self.viewmodel.on_initialize()
        self.viewmodel.refresh_data()
        
        # 设置默认显示状态（Grammar为默认选中）
        self.grammar_section.opacity = 1
        self.grammar_section.size_hint_y = 1
        self.vocab_section.opacity = 0
        self.vocab_section.size_hint_y = None
        self.vocab_section.height = 0
        
        # 强制刷新数据
        Clock.schedule_once(self._force_refresh_data, 0.5)
    
    def _force_refresh_data(self, dt):
        """强制刷新数据"""
        print("🔄 LearnScreen: 强制刷新数据...")
        self.viewmodel.refresh_data()
    
    def _on_grammar_rules_changed(self, instance, value):
        """Handle grammar rules data change"""
        self._update_grammar_cards(value)
    
    def _on_vocab_expressions_changed(self, instance, value):
        """Handle vocabulary expressions data change"""
        self._update_vocab_cards(value)
    
    def _on_grammar_loading_changed(self, instance, value):
        """Handle grammar loading state change"""
        if value:
            # Show loading state
            self._show_grammar_loading()
        else:
            # Hide loading state
            self._hide_grammar_loading()
    
    def _on_vocab_loading_changed(self, instance, value):
        """Handle vocabulary loading state change"""
        if value:
            # Show loading state
            self._show_vocab_loading()
        else:
            # Hide loading state
            self._hide_vocab_loading()
    
    def _on_grammar_error_changed(self, instance, value):
        """Handle grammar error state change"""
        if value:
            self._show_grammar_error(value)
    
    def _on_vocab_error_changed(self, instance, value):
        """Handle vocabulary error state change"""
        if value:
            self._show_vocab_error(value)
    
    def _on_total_grammar_rules_changed(self, instance, value):
        """Handle total grammar rules change"""
        self.grammar_stats.text = f"[color=000000]Grammar Rules: {value}[/color]"
    
    def _on_total_vocab_expressions_changed(self, instance, value):
        """Handle total vocabulary expressions change"""
        self.vocab_stats.text = f"[color=000000]Vocabulary: {value}[/color]"
    
    def _update_grammar_cards(self, grammar_rules):
        """Update grammar cards"""
        print(f"📝 LearnScreen: 更新语法卡片，数据数量: {len(grammar_rules) if grammar_rules else 0}")
        self.grammar_container.clear_widgets()
        
        if not grammar_rules:
            # Show empty state
            empty_label = FontUtils.create_label_with_chinese_support(
                text="[color=666666]No grammar rules available[/color]",
                markup=True, font_size=28, size_hint_y=None, height=100,
                halign='center', valign='middle'
            )
            self.grammar_container.add_widget(empty_label)
            print("📝 LearnScreen: Showing grammar rules empty state")
            return
        
        # Add grammar cards
        for i, rule_data in enumerate(grammar_rules):
            print(f"📝 LearnScreen: Adding grammar card {i+1}: {rule_data.get('name', 'Unknown')}")
            card = GrammarRuleCard(
                rule_data=rule_data,
                on_press_callback=lambda rd=rule_data: self._on_grammar_card_press(rd)
            )
            self.grammar_container.add_widget(card)
        
        print(f"📝 LearnScreen: Grammar cards update completed, total {len(grammar_rules)} cards")
    
    def _update_vocab_cards(self, vocab_expressions):
        """Update vocabulary cards"""
        print(f"📝 LearnScreen: 更新词汇卡片，数据数量: {len(vocab_expressions) if vocab_expressions else 0}")
        self.vocab_container.clear_widgets()
        
        if not vocab_expressions:
            # Show empty state
            empty_label = FontUtils.create_label_with_chinese_support(
                text="[color=666666]No vocabulary expressions available[/color]",
                markup=True, font_size=28, size_hint_y=None, height=100,
                halign='center', valign='middle'
            )
            self.vocab_container.add_widget(empty_label)
            print("📝 LearnScreen: Showing vocabulary expressions empty state")
            return
        
        # Add vocabulary cards
        for i, vocab_data in enumerate(vocab_expressions):
            print(f"📝 LearnScreen: Adding vocabulary card {i+1}: {vocab_data.get('name', 'Unknown')}")
            card = VocabExpressionCard(
                vocab_data=vocab_data,
                on_press_callback=lambda vd=vocab_data: self._on_vocab_card_press(vd)
            )
            self.vocab_container.add_widget(card)
        
        print(f"📝 LearnScreen: Vocabulary cards update completed, total {len(vocab_expressions)} cards")
    
    def _show_grammar_loading(self):
        """Show grammar loading state"""
        self.grammar_container.clear_widgets()
        loading_label = FontUtils.create_label_with_chinese_support(
            text="[color=000000]Loading grammar rules...[/color]",
            markup=True, font_size=28, size_hint_y=None, height=100,
            halign='center', valign='middle'
        )
        self.grammar_container.add_widget(loading_label)
    
    def _hide_grammar_loading(self):
        """Hide grammar loading state"""
        # Data will update automatically, no additional handling needed
        pass
    
    def _show_vocab_loading(self):
        """Show vocabulary loading state"""
        self.vocab_container.clear_widgets()
        loading_label = FontUtils.create_label_with_chinese_support(
            text="[color=000000]Loading vocabulary expressions...[/color]",
            markup=True, font_size=28, size_hint_y=None, height=100,
            halign='center', valign='middle'
        )
        self.vocab_container.add_widget(loading_label)
    
    def _hide_vocab_loading(self):
        """Hide vocabulary loading state"""
        # Data will update automatically, no additional handling needed
        pass
    
    def _show_grammar_error(self, error_message: str):
        """Show grammar error"""
        self.grammar_container.clear_widgets()
        error_label = FontUtils.create_label_with_chinese_support(
            text=f"[color=FF0000]Failed to load grammar rules: {error_message}[/color]",
            markup=True, font_size=24, size_hint_y=None, height=100,
            halign='center', valign='middle'
        )
        self.grammar_container.add_widget(error_label)
    
    def _show_vocab_error(self, error_message: str):
        """Show vocabulary error"""
        self.vocab_container.clear_widgets()
        error_label = FontUtils.create_label_with_chinese_support(
            text=f"[color=FF0000]Failed to load vocabulary expressions: {error_message}[/color]",
            markup=True, font_size=24, size_hint_y=None, height=100,
            halign='center', valign='middle'
        )
        self.vocab_container.add_widget(error_label)
    
    def _on_search_text_change(self, text: str):
        """Handle search text change"""
        self.viewmodel.set_search_text(text)
    
    def _on_category_filter_change(self, category: str):
        """Handle category filter change"""
        # Update button states
        self.grammar_button.set_selected(category == "grammar")
        self.vocab_button.set_selected(category == "vocab")
        
        # Show/hide sections based on category
        if category == "grammar":
            self.grammar_section.opacity = 1
            self.grammar_section.size_hint_y = 1
            self.vocab_section.opacity = 0
            self.vocab_section.size_hint_y = None
            self.vocab_section.height = 0
        elif category == "vocab":
            self.grammar_section.opacity = 0
            self.grammar_section.size_hint_y = None
            self.grammar_section.height = 0
            self.vocab_section.opacity = 1
            self.vocab_section.size_hint_y = 1
        
        # Update filter
        self.viewmodel.set_category_filter(category)
    
    def _on_read_tab_press(self, instance=None):
        """Handle Read tab press"""
        if self.manager:
            self.manager.current = "main"
    
    def _on_learn_tab_press(self, instance=None):
        """Handle Learn tab press"""
        # Already on Learn screen, do nothing
        pass
    
    def _on_grammar_card_press(self, rule_data: dict):
        """Handle grammar card press"""
        rule_id = rule_data.get("rule_id")
        print(f"Clicked grammar rule: {rule_id}")
        # TODO: Navigate to grammar detail page
        # self.manager.switch_to_screen("grammar_detail_screen", rule_id=rule_id)
    
    def _on_vocab_card_press(self, vocab_data: dict):
        """Handle vocabulary card press"""
        vocab_id = vocab_data.get("vocab_id")
        print(f"Clicked vocabulary expression: {vocab_id}")
        
        # 获取完整的词汇数据
        vocab_bundles = self.viewmodel.get_data("vocab_bundles")
        
        # 尝试不同的ID格式
        vocab_bundle = None
        if vocab_bundles:
            # 尝试字符串格式
            if str(vocab_id) in vocab_bundles:
                vocab_bundle = vocab_bundles[str(vocab_id)]
            # 尝试整数格式
            elif vocab_id in vocab_bundles:
                vocab_bundle = vocab_bundles[vocab_id]
        
        if vocab_bundle:
            # 创建词汇数据字典
            vocab_detail_data = {
                'vocab_id': vocab_bundle.vocab.vocab_id,
                'vocab_body': vocab_bundle.vocab.vocab_body,
                'explanation': vocab_bundle.vocab.explanation,
                'examples': []
            }
            
            # 添加示例数据
            for example in vocab_bundle.example:
                example_data = {
                    'text_id': example.text_id,
                    'sentence_id': example.sentence_id,
                    'context_explanation': example.context_explanation
                }
                vocab_detail_data['examples'].append(example_data)
            
            # 创建词汇详情页面并传递数据
            from ui.screens.vocab_detail_screen import VocabDetailScreen
            
            # 检查是否已存在词汇详情页面
            existing_screen = None
            for screen in self.manager.screens:
                if screen.name == 'vocab_detail_screen':
                    existing_screen = screen
                    break
            
            if existing_screen:
                # 如果已存在，更新数据并切换到该页面
                existing_screen.vocab_data = vocab_detail_data
                existing_screen.load_vocab_data()
                self.manager.current = 'vocab_detail_screen'
            else:
                # 如果不存在，创建新页面
                vocab_detail_screen = VocabDetailScreen(vocab_data=vocab_detail_data)
                vocab_detail_screen.name = 'vocab_detail_screen'
                self.manager.add_widget(vocab_detail_screen)
                self.manager.current = 'vocab_detail_screen'
        else:
            print(f"⚠️ Vocabulary data not found for ID: {vocab_id}")
            print(f"⚠️ Available IDs: {list(vocab_bundles.keys()) if vocab_bundles else 'None'}")
    
    def on_enter(self):
        """Called when entering the screen"""
        super().on_enter()
        # Refresh data
        self.viewmodel.refresh_data()
    
    def on_leave(self):
        """Called when leaving the screen"""
        super().on_leave()
        # Cleanup resources
        pass
    
    def on_destroy(self):
        """Called when destroying"""
        if self.viewmodel:
            self.viewmodel.destroy()
        super().on_destroy() 