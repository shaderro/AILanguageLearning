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
        title = Label(
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
        
        self.all_button = CategoryFilterButton(
            "All", "all", True, self._on_category_filter_change
        )
        self.grammar_button = CategoryFilterButton(
            "Grammar", "grammar", False, self._on_category_filter_change
        )
        self.vocab_button = CategoryFilterButton(
            "Vocabulary", "vocab", False, self._on_category_filter_change
        )
        
        filter_layout.add_widget(self.all_button)
        filter_layout.add_widget(self.grammar_button)
        filter_layout.add_widget(self.vocab_button)
        main_layout.add_widget(filter_layout)
        
        # Statistics
        stats_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        self.grammar_stats = Label(
            text="[color=000000]Grammar Rules: 0[/color]",
            markup=True, font_size=24, halign='left', valign='middle'
        )
        self.vocab_stats = Label(
            text="[color=000000]Vocabulary: 0[/color]",
            markup=True, font_size=24, halign='right', valign='middle'
        )
        
        stats_layout.add_widget(self.grammar_stats)
        stats_layout.add_widget(self.vocab_stats)
        main_layout.add_widget(stats_layout)
        
        # Content area
        content_layout = BoxLayout(orientation='vertical', spacing=15)
        
        # Grammar rules section
        grammar_section = self._build_grammar_section()
        content_layout.add_widget(grammar_section)
        
        # Vocabulary expressions section
        vocab_section = self._build_vocab_section()
        content_layout.add_widget(vocab_section)
        
        # Scroll view
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(content_layout)
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
        grammar_title = Label(
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
        
        # Grammar scroll view
        grammar_scroll = ScrollView(size_hint=(1, None), height=400)
        grammar_scroll.add_widget(self.grammar_container)
        section.add_widget(grammar_scroll)
        
        return section
    
    def _build_vocab_section(self) -> BoxLayout:
        """Build vocabulary expressions section"""
        section = BoxLayout(orientation='vertical', spacing=10)
        
        # Title
        vocab_title = Label(
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
        
        # Vocabulary scroll view
        vocab_scroll = ScrollView(size_hint=(1, None), height=400)
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
        self.viewmodel.on_initialize()
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
        self.grammar_container.clear_widgets()
        
        if not grammar_rules:
            # Show empty state
            empty_label = Label(
                text="[color=666666]No grammar rules available[/color]",
                markup=True, font_size=28, size_hint_y=None, height=100,
                halign='center', valign='middle'
            )
            self.grammar_container.add_widget(empty_label)
            return
        
        # Add grammar cards
        for rule_data in grammar_rules:
            card = GrammarRuleCard(
                rule_data=rule_data,
                on_press_callback=lambda rd=rule_data: self._on_grammar_card_press(rd)
            )
            self.grammar_container.add_widget(card)
    
    def _update_vocab_cards(self, vocab_expressions):
        """Update vocabulary cards"""
        self.vocab_container.clear_widgets()
        
        if not vocab_expressions:
            # Show empty state
            empty_label = Label(
                text="[color=666666]No vocabulary expressions available[/color]",
                markup=True, font_size=28, size_hint_y=None, height=100,
                halign='center', valign='middle'
            )
            self.vocab_container.add_widget(empty_label)
            return
        
        # Add vocabulary cards
        for vocab_data in vocab_expressions:
            card = VocabExpressionCard(
                vocab_data=vocab_data,
                on_press_callback=lambda vd=vocab_data: self._on_vocab_card_press(vd)
            )
            self.vocab_container.add_widget(card)
    
    def _show_grammar_loading(self):
        """Show grammar loading state"""
        self.grammar_container.clear_widgets()
        loading_label = Label(
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
        loading_label = Label(
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
        error_label = Label(
            text=f"[color=FF0000]Failed to load grammar rules: {error_message}[/color]",
            markup=True, font_size=24, size_hint_y=None, height=100,
            halign='center', valign='middle'
        )
        self.grammar_container.add_widget(error_label)
    
    def _show_vocab_error(self, error_message: str):
        """Show vocabulary error"""
        self.vocab_container.clear_widgets()
        error_label = Label(
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
        self.all_button.set_selected(category == "all")
        self.grammar_button.set_selected(category == "grammar")
        self.vocab_button.set_selected(category == "vocab")
        
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
        # TODO: Navigate to vocabulary detail page
        # self.manager.switch_to_screen("vocab_detail_screen", vocab_id=vocab_id)
    
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