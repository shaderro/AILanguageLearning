"""
Main screen module
Contains the main interface of the application
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle
from functools import partial

# Import components - use absolute imports
try:
    from components.cards import ClickableCard, VocabCard
    from components.buttons import TabButton, SubTabButton, BottomTabBar
    from utils.swipe_handler import SwipeHandler
    from viewmodels.article_list_viewmodel import ArticleListViewModel
except ImportError:
    # If running this file directly, use relative imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from components.cards import ClickableCard, VocabCard
    from components.buttons import TabButton, SubTabButton, BottomTabBar
    from utils.swipe_handler import SwipeHandler
    from viewmodels.article_list_viewmodel import ArticleListViewModel


class MainScreen(Screen):
    """Main screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.swipe_handler = SwipeHandler()
        
        # Initialize ViewModel
        self.article_viewmodel = ArticleListViewModel()
        
        # Initialize data managers for real grammar and vocabulary data
        self.grammar_manager = None
        self.vocab_manager = None
        self._initialize_data_managers()
        
        # Store card references
        self.article_cards = []
        self.vocab_cards = []
        
        self._setup_background()
        self._setup_layout()
        #self._setup_topbar()
        self._setup_reading_page()
        self._setup_learn_page()
        self._setup_tab_bar()
        
        # Initially show reading cards
        self.show_tab1()
    
    def _initialize_data_managers(self):
        """Initialize grammar and vocabulary data managers"""
        try:
            print("📚 Initializing data managers for real grammar and vocabulary data...")
            
            # Import data managers
            from data_managers.grammar_rule_manager import GrammarRuleManager
            from data_managers.vocab_manager import VocabManager
            
            # Create managers
            self.grammar_manager = GrammarRuleManager()
            self.vocab_manager = VocabManager()
            
            # Load data from files
            try:
                self.grammar_manager.load_from_file("data/grammar_rules.json")
                print(f"✅ Loaded {len(self.grammar_manager.grammar_bundles)} grammar rules")
            except Exception as e:
                print(f"⚠️ Failed to load grammar rules: {e}")
            
            try:
                self.vocab_manager.load_from_file("data/vocab_expressions.json")
                print(f"✅ Loaded {len(self.vocab_manager.vocab_bundles)} vocabulary expressions")
            except Exception as e:
                print(f"⚠️ Failed to load vocabulary expressions: {e}")
            
        except Exception as e:
            print(f"❌ Error initializing data managers: {e}")
            self.grammar_manager = None
            self.vocab_manager = None
    
    def _setup_background(self):
        """Setup background"""
        with self.canvas.before:
            Color(1, 1, 1, 1)  # White background
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
    
    def _setup_layout(self):
        """Setup main layout"""
        # Main container: vertical layout containing content area and tab bar
        self.layout = BoxLayout(orientation='vertical')
        
        # Content area: use single container, dynamically switch content
        self.content_container = BoxLayout(orientation='vertical', size_hint_y=1)
        self.layout.add_widget(self.content_container)
        
        self.add_widget(self.layout)
    
    def _setup_topbar(self):
        """Setup top bar"""
        topbar = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, padding=20)
        topbar.add_widget(Label(text="≡", font_size=48, size_hint_x=None, width=80, color=(0, 0, 0, 1)))
        topbar.add_widget(Widget())
        self.layout.add_widget(topbar)
    
    def _setup_reading_page(self):
        """Setup card list - use ViewModel to load real data"""
        # Get article data from ViewModel
        articles = self.article_viewmodel.load_articles()
        
        # Create card for each article
        for article in articles:
            card = ClickableCard(
                article.title, 
                article.word_count, 
                article.level, 
                article.progress_percent, 
                on_press_callback=partial(self.open_article, article.text_id)
            )
            self.article_cards.append(card)
            print(f"📚 Created article card: {article.title} (ID: {article.text_id})")
    
    def _setup_learn_page(self):
        """Setup learning page content area - includes sub tab bar and content area"""
        # Learning page container
        self.learn_content_container = BoxLayout(orientation='vertical', size_hint_y=1)
        
        # Add border to learning container
        with self.learn_content_container.canvas.before:
            Color(0, 0, 0, 1)  # Black border
            self.learn_border = Rectangle(pos=self.learn_content_container.pos, size=self.learn_content_container.size)
        self.learn_content_container.bind(pos=self._update_learn_border, size=self._update_learn_border)
        
        # Setup sub tab bar
        self._setup_learn_sub_tab_bar()
        
        # Setup content area
        self._setup_learn_content_area()
    
    def _setup_learn_sub_tab_bar(self):
        """Setup learning sub tab bar"""
        # Sub tab bar container
        sub_tab_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10, padding=20)
        
        # Add border to sub tab bar
        with sub_tab_container.canvas.before:
            Color(0, 0, 0, 1)  # Black border
            self.sub_tab_border = Rectangle(pos=sub_tab_container.pos, size=sub_tab_container.size)
        sub_tab_container.bind(pos=self._update_sub_tab_border, size=self._update_sub_tab_border)
        
        # Create sub tab buttons
        self.sub_tab1_btn = SubTabButton('Grammar', is_active=True)
        self.sub_tab2_btn = SubTabButton('Vocabulary', is_active=False)
        
        self.sub_tab1_btn.bind(on_release=self.show_grammar_content)
        self.sub_tab2_btn.bind(on_release=self.show_vocab_content)
        
        sub_tab_container.add_widget(self.sub_tab1_btn)
        sub_tab_container.add_widget(self.sub_tab2_btn)
        
        self.learn_content_container.add_widget(sub_tab_container)
    
    def _setup_learn_content_area(self):
        """Setup learning content area"""
        # Content area container
        content_area = BoxLayout(orientation='vertical', size_hint_y=1, padding=20)
        
        # Add border to content area
        with content_area.canvas.before:
            Color(0, 0, 0, 1)  # Black border
            self.content_border = Rectangle(pos=content_area.pos, size=content_area.size)
        content_area.bind(pos=self._update_content_border, size=self._update_content_border)
        
        # Scroll view for content
        self.learn_scroll = ScrollView(size_hint_y=1)
        
        # Add border to scroll view
        with self.learn_scroll.canvas.before:
            Color(0, 0, 0, 1)  # Black border
            self.scroll_border = Rectangle(pos=self.learn_scroll.pos, size=self.learn_scroll.size)
        self.learn_scroll.bind(pos=self._update_scroll_border, size=self._update_scroll_border)
        
        # Learning container
        self.learn_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15)
        self.learn_container.bind(minimum_height=self.learn_container.setter('height'))
        
        self.learn_scroll.add_widget(self.learn_container)
        content_area.add_widget(self.learn_scroll)
        
        self.learn_content_container.add_widget(content_area)
    
    def show_grammar_content(self, *args):
        """Show grammar content with real data"""
        self.sub_tab1_btn.set_active(True)
        self.sub_tab2_btn.set_active(False)
        
        # Clear container
        self.learn_container.clear_widgets()
        
        if self.grammar_manager and self.grammar_manager.grammar_bundles:
            # Use real grammar data
            print(f"📚 Loading {len(self.grammar_manager.grammar_bundles)} grammar rules...")
            
            for rule_id, bundle in self.grammar_manager.grammar_bundles.items():
                rule = bundle.rule
                examples = bundle.examples
                
                # Get example sentence if available
                example_text = "No example available"
                if examples:
                    # Use the first example
                    example = examples[0]
                    # Try to get the sentence from text manager
                    try:
                        from data_managers.original_text_manager import OriginalTextManager
                        text_manager = OriginalTextManager()
                        text_manager.load_from_file("data/original_texts.json")
                        sentence = text_manager.get_sentence_by_id(example.text_id, example.sentence_id)
                        if sentence:
                            example_text = sentence.sentence_body
                    except Exception as e:
                        print(f"⚠️ Could not load example sentence: {e}")
                
                # Determine difficulty based on rule complexity
                difficulty = self._determine_grammar_difficulty(rule.explanation)
                
                # Create grammar card
                card = VocabCard(
                    rule.name,
                    rule.explanation,
                    example_text,
                    difficulty,
                    on_press_callback=partial(self.open_grammar_detail, rule.name, rule.explanation, example_text, difficulty)
                )
                self.learn_container.add_widget(card)
                print(f"📝 Added grammar card: {rule.name}")
        else:
            # Fallback to hardcoded data if no real data available
            print("⚠️ No real grammar data available, using fallback data")
            grammar_cards = [
                VocabCard("Present Perfect", "Used for actions completed in the past with present relevance", 
                         "I have finished my homework.", "medium"),
                VocabCard("Past Continuous", "Used for actions in progress at a specific time in the past", 
                         "I was reading when she called.", "easy"),
                VocabCard("Future Perfect", "Used for actions that will be completed before a future time", 
                         "By next week, I will have finished the project.", "hard")
            ]
            
            for card in grammar_cards:
                self.learn_container.add_widget(card)
    
    def show_vocab_content(self, *args):
        """Show vocabulary content with real data"""
        self.sub_tab1_btn.set_active(False)
        self.sub_tab2_btn.set_active(True)
        
        # Clear container
        self.learn_container.clear_widgets()
        
        if self.vocab_manager and self.vocab_manager.vocab_bundles:
            # Use real vocabulary data
            print(f"📚 Loading {len(self.vocab_manager.vocab_bundles)} vocabulary expressions...")
            
            for vocab_id, bundle in self.vocab_manager.vocab_bundles.items():
                vocab = bundle.vocab
                examples = bundle.example
                
                # Get example sentence if available
                example_text = "No example available"
                if examples:
                    # Use the first example
                    example = examples[0]
                    # Try to get the sentence from text manager
                    try:
                        from data_managers.original_text_manager import OriginalTextManager
                        text_manager = OriginalTextManager()
                        text_manager.load_from_file("data/original_texts.json")
                        sentence = text_manager.get_sentence_by_id(example.text_id, example.sentence_id)
                        if sentence:
                            example_text = sentence.sentence_body
                    except Exception as e:
                        print(f"⚠️ Could not load example sentence: {e}")
                
                # Determine difficulty based on vocabulary complexity
                difficulty = self._determine_vocab_difficulty(vocab.vocab_body, vocab.explanation)
                
                # Create vocabulary card
                card = VocabCard(
                    vocab.vocab_body,
                    vocab.explanation,
                    example_text,
                    difficulty,
                    on_press_callback=partial(self.open_vocab_detail, vocab.vocab_body, vocab.explanation, example_text, difficulty)
                )
                self.learn_container.add_widget(card)
                print(f"📝 Added vocabulary card: {vocab.vocab_body}")
        else:
            # Fallback to hardcoded data if no real data available
            print("⚠️ No real vocabulary data available, using fallback data")
            vocab_cards = [
                VocabCard("Serendipity", "The occurrence and development of events by chance in a happy or beneficial way", 
                         "Finding that book was pure serendipity.", "hard"),
                VocabCard("Ubiquitous", "Present, appearing, or found everywhere", 
                         "Mobile phones have become ubiquitous in modern society.", "medium"),
                VocabCard("Ephemeral", "Lasting for a very short time", 
                         "The beauty of cherry blossoms is ephemeral.", "medium")
            ]
            
            for card in vocab_cards:
                self.learn_container.add_widget(card)
    
    def _setup_tab_bar(self):
        """Setup tab bar"""
        # Use unified BottomTabBar component
        self.tab_bar = BottomTabBar(
            read_callback=self.show_tab1,
            learn_callback=self.show_tab2,
            active_tab="read"
        )
        self.layout.add_widget(self.tab_bar)
    
    def _update_bg(self, *args):
        """Update background"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def _update_content_border(self, *args):
        """Update content area border"""
        if hasattr(self, 'content_border'):
            self.content_border.pos = self.learn_content_container.children[0].pos
            self.content_border.size = self.learn_content_container.children[0].size
    
    def open_article(self, text_id):
        print(f"Clicked article: {text_id}")
        # Get article details from ViewModel
        article = self.article_viewmodel.get_article_by_id(text_id)
        if article:
            print(f"📖 Loading article: {article.text_title}")
            # Navigate to text_input_chat page and pass article data
            if self.manager:
                textinput_screen = self.manager.get_screen("textinput_chat")
                # Set article data
                textinput_screen.set_article(article)
                self.manager.current = "textinput_chat"
        else:
            print(f"❌ Article not found ID: {text_id}")
    
    def show_tab1(self, *args):
        """Show tab 1 - Article list"""
        # Update tab bar state
        self.tab_bar.set_active_tab("read")
        
        # Clear container
        self.content_container.clear_widgets()
        
        # Create scroll view for article list
        article_scroll = ScrollView(size_hint_y=1)
        article_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=20, padding=20)
        article_container.bind(minimum_height=lambda instance, value: setattr(article_container, 'height', value))
        
        # Add article cards - first remove cards, then re-add
        for card in self.article_cards:
            # If card already has parent container, remove first
            if card.parent:
                card.parent.remove_widget(card)
            article_container.add_widget(card)
        
        article_scroll.add_widget(article_container)
        self.content_container.add_widget(article_scroll)
    
    def show_tab2(self, *args):
        """Show tab 2 - Learning page"""
        # Update tab bar state
        self.tab_bar.set_active_tab("learn")
        
        # Navigate to Learn screen instead of using built-in learn page
        if self.manager:
            self.manager.current = "learn_screen"
    
    def _update_learn_border(self, *args):
        """Update learning page border"""
        self.learn_border.pos = self.learn_content_container.pos
        self.learn_border.size = self.learn_content_container.size

    def _update_sub_tab_border(self, *args):
        """Update sub tab bar border"""
        if hasattr(self, 'sub_tab_border'):
            self.sub_tab_border.pos = self.sub_tab1_btn.parent.pos
            self.sub_tab_border.size = self.sub_tab1_btn.parent.size

    def _update_scroll_border(self, *args):
        """Update scroll area border"""
        if hasattr(self, 'scroll_border'):
            self.scroll_border.pos = self.learn_scroll.pos
            self.scroll_border.size = self.learn_scroll.size

    def open_vocab_detail(self, word, meaning, example, difficulty):
        """Navigate to vocabulary detail page"""
        if self.manager:
            vocab_screen = self.manager.get_screen("vocab_detail")
            # Can pass data here, expandable later
            # vocab_screen.set_vocab(word, meaning, example, difficulty)
            self.manager.current = "vocab_detail"

    def open_grammar_detail(self, rule_name, explanation, example, difficulty):
        """Navigate to grammar detail page"""
        if self.manager:
            grammar_screen = self.manager.get_screen("grammar_detail")
            # Can pass data here, expandable later
            # grammar_screen.set_grammar(rule_name, explanation, example, difficulty)
            self.manager.current = "grammar_detail"
    
    def _determine_grammar_difficulty(self, explanation):
        """Determine grammar rule difficulty based on explanation"""
        # Simple heuristic based on explanation length and complexity
        if len(explanation) < 50:
            return "easy"
        elif len(explanation) < 100:
            return "medium"
        else:
            return "hard"
    
    def _determine_vocab_difficulty(self, vocab_body, explanation):
        """Determine vocabulary difficulty based on word and explanation"""
        # Simple heuristic based on word length and explanation complexity
        if len(vocab_body) <= 5 and len(explanation) < 50:
            return "easy"
        elif len(vocab_body) <= 8 and len(explanation) < 100:
            return "medium"
        else:
            return "hard"


# Test application
if __name__ == '__main__':
    from kivy.app import App
    
    class TestApp(App):
        def build(self):
            return MainScreen()
    
    TestApp().run() 