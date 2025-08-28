"""
Learn screen ViewModel
Manages data binding for grammar and vocabulary cards
"""

from typing import List, Dict, Any, Optional
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from ui.viewmodels.base_viewmodel import BaseViewModel
from data_managers.data_classes import GrammarBundle, VocabExpressionBundle


class LearnScreenViewModel(BaseViewModel):
    """Learn screen ViewModel"""
    
    # Grammar properties
    grammar_rules = ListProperty([])
    grammar_loading = BooleanProperty(False)
    grammar_error = StringProperty("")
    
    # Vocabulary properties
    vocab_expressions = ListProperty([])
    vocab_loading = BooleanProperty(False)
    vocab_error = StringProperty("")
    
    # Filter and search properties
    search_text = StringProperty("")
    selected_category = StringProperty("grammar")  # "grammar", "vocab"
    
    # Statistics
    total_grammar_rules = NumericProperty(0)
    total_vocab_expressions = NumericProperty(0)
    
    def __init__(self, name: str = "LearnScreenViewModel", data_binding_service=None, **kwargs):
        super().__init__(name, data_binding_service=data_binding_service, **kwargs)
        self._grammar_bundles: Dict[int, GrammarBundle] = {}
        self._vocab_bundles: Dict[int, VocabExpressionBundle] = {}
    
    def on_initialize(self):
        """Initialize data binding"""
        super().on_initialize()
        
        # Bind grammar data
        self.bind_to_data_service("grammar_bundles", "grammar_rules", self._transform_grammar_bundles)
        self.bind_to_data_service("grammar_loading", "grammar_loading")
        self.bind_to_data_service("grammar_error", "grammar_error")
        
        # Bind vocabulary data
        self.bind_to_data_service("vocab_bundles", "vocab_expressions", self._transform_vocab_bundles)
        self.bind_to_data_service("vocab_loading", "vocab_loading")
        self.bind_to_data_service("vocab_error", "vocab_error")
        
        # Bind statistics
        self.bind_to_data_service("total_grammar_rules", "total_grammar_rules")
        self.bind_to_data_service("total_vocab_expressions", "total_vocab_expressions")
    
    def load_grammar_rules(self):
        """Load grammar rules"""
        try:
            self.set_loading(True)
            self.clear_error()
            
            # Get grammar data from data service
            grammar_bundles = self.get_data("grammar_bundles")
            if grammar_bundles:
                self._grammar_bundles = grammar_bundles
                self._update_grammar_rules_display()
            
            self.set_loading(False)
            
        except Exception as e:
            self.set_loading(False)
            self.set_error(f"Failed to load grammar rules: {str(e)}")
    
    def load_vocab_expressions(self):
        """Load vocabulary expressions"""
        try:
            self.set_loading(True)
            self.clear_error()
            
            # Get vocabulary data from data service
            vocab_bundles = self.get_data("vocab_bundles")
            if vocab_bundles:
                self._vocab_bundles = vocab_bundles
                self._update_vocab_expressions_display()
            
            self.set_loading(False)
            
        except Exception as e:
            self.set_loading(False)
            self.set_error(f"Failed to load vocabulary expressions: {str(e)}")
    
    def _transform_grammar_bundles(self, grammar_bundles):
        """Transform grammar bundles to display format"""
        if not grammar_bundles:
            return []
        
        display_rules = []
        for rule_id, bundle in grammar_bundles.items():
            rule_data = {
                "rule_id": rule_id,
                "name": bundle.rule.name,
                "explanation": bundle.rule.explanation,
                "example_count": len(bundle.examples),
                "difficulty": self._calculate_grammar_difficulty(bundle)
            }
            display_rules.append(rule_data)
        
        # Apply search and filter
        filtered_rules = self._filter_grammar_rules(display_rules)
        self.total_grammar_rules = len(display_rules)
        return filtered_rules
    
    def _transform_vocab_bundles(self, vocab_bundles):
        """Transform vocabulary bundles to display format"""
        if not vocab_bundles:
            return []
        
        display_vocabs = []
        for vocab_id, bundle in vocab_bundles.items():
            vocab_data = {
                "vocab_id": vocab_id,
                "name": bundle.vocab.vocab_body,  # Use vocab_body as name
                "body": bundle.vocab.vocab_body,
                "explanation": bundle.vocab.explanation,
                "example_count": len(bundle.example),
                "difficulty": self._calculate_vocab_difficulty(bundle)
            }
            display_vocabs.append(vocab_data)
        
        # Apply search and filter
        filtered_vocabs = self._filter_vocab_expressions(display_vocabs)
        self.total_vocab_expressions = len(display_vocabs)
        return filtered_vocabs
    
    def _update_grammar_rules_display(self):
        """Update grammar rules display data"""
        display_rules = []
        
        for rule_id, bundle in self._grammar_bundles.items():
            rule_data = {
                "rule_id": rule_id,
                "name": bundle.rule.name,
                "explanation": bundle.rule.explanation,
                "example_count": len(bundle.examples),
                "difficulty": self._calculate_grammar_difficulty(bundle)
            }
            display_rules.append(rule_data)
        
        # Apply search and filter
        filtered_rules = self._filter_grammar_rules(display_rules)
        self.grammar_rules = filtered_rules
        self.total_grammar_rules = len(display_rules)
    
    def _update_vocab_expressions_display(self):
        """Update vocabulary expressions display data"""
        display_vocabs = []
        
        for vocab_id, bundle in self._vocab_bundles.items():
            vocab_data = {
                "vocab_id": vocab_id,
                "name": bundle.vocab.vocab_body,  # Use vocab_body as name
                "body": bundle.vocab.vocab_body,
                "explanation": bundle.vocab.explanation,
                "example_count": len(bundle.example),
                "difficulty": self._calculate_vocab_difficulty(bundle)
            }
            display_vocabs.append(vocab_data)
        
        # Apply search and filter
        filtered_vocabs = self._filter_vocab_expressions(display_vocabs)
        self.vocab_expressions = filtered_vocabs
        self.total_vocab_expressions = len(display_vocabs)
    
    def _calculate_grammar_difficulty(self, bundle: GrammarBundle) -> str:
        """Calculate grammar rule difficulty"""
        example_count = len(bundle.examples)
        if example_count >= 3:
            return "easy"
        elif example_count >= 1:
            return "medium"
        else:
            return "hard"
    
    def _calculate_vocab_difficulty(self, bundle: VocabExpressionBundle) -> str:
        """Calculate vocabulary difficulty"""
        example_count = len(bundle.example)
        vocab_length = len(bundle.vocab.vocab_body)
        
        if example_count >= 2 and vocab_length <= 10:
            return "easy"
        elif example_count >= 1 and vocab_length <= 15:
            return "medium"
        else:
            return "hard"
    
    def _filter_grammar_rules(self, rules: List[Dict]) -> List[Dict]:
        """Filter grammar rules"""
        if self.selected_category != "grammar":
            return []
        
        if not self.search_text:
            return rules
        
        filtered = []
        search_lower = self.search_text.lower()
        
        for rule in rules:
            if (search_lower in rule["name"].lower() or 
                search_lower in rule["explanation"].lower()):
                filtered.append(rule)
        
        return filtered
    
    def _filter_vocab_expressions(self, vocabs: List[Dict]) -> List[Dict]:
        """Filter vocabulary expressions"""
        if self.selected_category != "vocab":
            return []
        
        if not self.search_text:
            return vocabs
        
        filtered = []
        search_lower = self.search_text.lower()
        
        for vocab in vocabs:
            if (search_lower in vocab["vocab_body"].lower() or 
                search_lower in vocab["explanation"].lower()):
                filtered.append(vocab)
        
        return filtered
    
    def set_search_text(self, text: str):
        """Set search text"""
        self.search_text = text
        self._update_grammar_rules_display()
        self._update_vocab_expressions_display()
    
    def set_category_filter(self, category: str):
        """Set category filter"""
        self.selected_category = category
        self._update_grammar_rules_display()
        self._update_vocab_expressions_display()
    
    def get_grammar_rule_by_id(self, rule_id: int) -> Optional[Dict]:
        """Get grammar rule details by ID"""
        if rule_id in self._grammar_bundles:
            bundle = self._grammar_bundles[rule_id]
            return {
                "rule_id": rule_id,
                "name": bundle.rule.name,
                "explanation": bundle.rule.explanation,
                "examples": bundle.examples
            }
        return None
    
    def get_vocab_expression_by_id(self, vocab_id: int) -> Optional[Dict]:
        """Get vocabulary expression details by ID"""
        if vocab_id in self._vocab_bundles:
            bundle = self._vocab_bundles[vocab_id]
            return {
                "vocab_id": vocab_id,
                "vocab_body": bundle.vocab.vocab_body,
                "explanation": bundle.vocab.explanation,
                "examples": bundle.example
            }
        return None
    
    def refresh_data(self):
        """Refresh all data"""
        print("🔄 LearnScreenViewModel: Starting data refresh...")
        
        # Get data directly from data service
        grammar_bundles = self.get_data("grammar_bundles")
        vocab_bundles = self.get_data("vocab_bundles")
        
        print(f"🔄 LearnScreenViewModel: Got grammar data: {type(grammar_bundles)}, count: {len(grammar_bundles) if grammar_bundles else 0}")
        print(f"🔄 LearnScreenViewModel: Got vocabulary data: {type(vocab_bundles)}, count: {len(vocab_bundles) if vocab_bundles else 0}")
        
        if grammar_bundles:
            self._grammar_bundles = grammar_bundles
            transformed_grammar = self._transform_grammar_bundles(grammar_bundles)
            self.grammar_rules = transformed_grammar
            print(f"🔄 LearnScreenViewModel: Grammar rules transformation completed, display count: {len(transformed_grammar)}")
        else:
            print("🔄 LearnScreenViewModel: No grammar data received")
        
        if vocab_bundles:
            self._vocab_bundles = vocab_bundles
            transformed_vocab = self._transform_vocab_bundles(vocab_bundles)
            self.vocab_expressions = transformed_vocab
            print(f"🔄 LearnScreenViewModel: Vocabulary expressions transformation completed, display count: {len(transformed_vocab)}")
        else:
            print("🔄 LearnScreenViewModel: No vocabulary data received")
        
        print("🔄 LearnScreenViewModel: Data refresh completed")
    
    def on_destroy(self):
        """Cleanup on destroy"""
        super().on_destroy()
        self._grammar_bundles.clear()
        self._vocab_bundles.clear() 