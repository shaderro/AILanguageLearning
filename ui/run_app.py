#!/usr/bin/env python3
"""
Language Learning App - Main startup file
Refactored modular application entry point with MainAssistant integration
"""

import os
import sys

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition

# Import refactored components
from ui.screens.main_screen import MainScreen
from ui.screens.reading_content_screen import ReadingContentScreen
from ui.screens.vocab_detail_screen import VocabDetailScreen
from ui.screens.grammar_detail_screen import GrammarDetailScreen
from ui.screens.reading_content_textinput_screen import ReadingContentTextInputScreen
# from ui.screens.text_input_chat_screen import TextInputChatScreen  # Commented out, using test version instead
from ui.screens.learn_screen import LearnScreen
# from ui.screens.read_content_screen import ReadContentScreen

# Import data binding services and managers
from ui.services.language_learning_binding_service import LanguageLearningBindingService
from data_managers.grammar_rule_manager import GrammarRuleManager
from data_managers.vocab_manager import VocabManager

class LangUIApp(App):
    """Language learning app main class with MainAssistant integration"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_binding_service = None
        self.grammar_manager = None
        self.vocab_manager = None
    
    def build(self):
        """Build application interface"""
        print("🚀 Building Language Learning App with MainAssistant integration...")
        
        # Initialize data binding service
        self._initialize_data_binding_service()
        
        # Load grammar and vocabulary data
        self._load_grammar_vocab_data()
        
        # Create screen manager
        sm = ScreenManager(transition=NoTransition())
        
        # Add screens
        main_screen = MainScreen(name="main")
        sm.add_widget(main_screen)
        
        read_screen = ReadingContentScreen(name="read")
        sm.add_widget(read_screen)
        
        textinput_screen = ReadingContentTextInputScreen(name="textinput_read")
        sm.add_widget(textinput_screen)
        
        # Enhanced TextInputChatScreen with MainAssistant integration
        # Use the test version which has better text rendering
        from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest
        textinput_chat_screen = TextInputChatScreenTest(name="textinput_chat")
        sm.add_widget(textinput_chat_screen)
        
        vocab_detail_screen = VocabDetailScreen(name="vocab_detail")
        sm.add_widget(vocab_detail_screen)
        
        grammar_detail_screen = GrammarDetailScreen(name="grammar_detail")
        sm.add_widget(grammar_detail_screen)
        
        # Add Learn screen with data binding service
        learn_screen = LearnScreen(data_binding_service=self.data_binding_service, name="learn")
        sm.add_widget(learn_screen)
        
        print("✅ Learn screen added with data binding service")
        
        print("✅ All screens initialized successfully")
        return sm
    
    def _initialize_data_binding_service(self):
        """Initialize data binding service"""
        self.data_binding_service = LanguageLearningBindingService()
        
        # Initialize grammar and vocabulary managers
        self.grammar_manager = GrammarRuleManager()
        self.vocab_manager = VocabManager()
        
        print("✅ Data binding service initialized")
    
    def _load_grammar_vocab_data(self):
        """Load grammar and vocabulary data"""
        # Note: Data binding service already loads data in its initialization
        # This method is kept for compatibility but data is already loaded
        print("📝 Note: Data binding service already loads data automatically")
        
        # Check if data is already loaded in binding service
        grammar_bundles = self.data_binding_service.get_data("grammar_bundles")
        vocab_bundles = self.data_binding_service.get_data("vocab_bundles")
        
        print(f"📊 Data binding service has {len(grammar_bundles) if grammar_bundles else 0} grammar rules")
        print(f"📊 Data binding service has {len(vocab_bundles) if vocab_bundles else 0} vocabulary expressions")
    
    def _register_data_to_binding_service(self):
        """Register data to binding service"""
        # Register grammar data
        grammar_bundles = self.grammar_manager.grammar_bundles
        self.data_binding_service.update_data("grammar_bundles", grammar_bundles)
        self.data_binding_service.update_data("grammar_loading", False)
        self.data_binding_service.update_data("grammar_error", "")
        self.data_binding_service.update_data("total_grammar_rules", len(grammar_bundles))
        
        # Register vocabulary data
        vocab_bundles = self.vocab_manager.vocab_bundles
        self.data_binding_service.update_data("vocab_bundles", vocab_bundles)
        self.data_binding_service.update_data("vocab_loading", False)
        self.data_binding_service.update_data("vocab_error", "")
        self.data_binding_service.update_data("total_vocab_expressions", len(vocab_bundles))
        
        print(f"✅ Data registered: {len(grammar_bundles)} grammar rules, {len(vocab_bundles)} vocabulary expressions")
    
    def on_stop(self):
        """Cleanup when app stops"""
        if self.data_binding_service:
            # Cleanup data binding service
            for viewmodel_name in list(self.data_binding_service._viewmodels.keys()):
                self.data_binding_service.unregister_viewmodel(viewmodel_name)
        print("👋 Language learning app stopped")

if __name__ == '__main__':
    import os, sys
    print("🚀 Starting language learning app with MainAssistant integration...")
    print("📁 Current working directory:", os.getcwd())
    print("🐍 Python version:", sys.version.split()[0])
    print("📦 Using enhanced modular structure with AI integration")
    print("-" * 50)
    LangUIApp().run()