"""
Learn screen card components
Includes grammar rule card and vocabulary expression card
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import StringProperty, NumericProperty
from ui.components.cards import BaseCard


class GrammarRuleCard(BaseCard):
    """Grammar rule card"""
    
    rule_name = StringProperty("")
    explanation = StringProperty("")
    example_count = NumericProperty(0)
    difficulty = StringProperty("medium")
    
    def __init__(self, rule_data: dict, on_press_callback=None, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=10, 
                        size_hint_y=None, height=200, **kwargs)
        
        self.rule_name = rule_data.get("name", "")
        self.explanation = rule_data.get("explanation", "")
        self.example_count = rule_data.get("example_count", 0)
        self.difficulty = rule_data.get("difficulty", "medium")
        self.on_press_callback = on_press_callback
        
        self._build_ui()
    
    def _build_ui(self):
        """Build UI"""
        # Header: title and difficulty
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        # Title
        title_label = Label(
            text=f"[b][color=000000]{self.rule_name}[/color][/b]",
            markup=True, font_size=32, halign='left', valign='middle',
            size_hint_x=0.7
        )
        header.add_widget(title_label)
        
        # Difficulty label
        difficulty_color = self._get_difficulty_color(self.difficulty)
        difficulty_label = Label(
            text=f"[color={difficulty_color}]{self.difficulty.upper()}[/color]",
            markup=True, font_size=24, size_hint_x=0.3,
            halign='right', valign='middle'
        )
        header.add_widget(difficulty_label)
        self.add_widget(header)
        
        # Explanation
        explanation_label = Label(
            text=f"[color=000000]{self.explanation[:100]}{'...' if len(self.explanation) > 100 else ''}[/color]",
            markup=True, font_size=26, halign='left', valign='top',
            size_hint_y=None, height=80, text_size=(self.width - 30, None)
        )
        self.add_widget(explanation_label)
        
        # Footer: example count and click hint
        footer = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        
        # Example count
        example_label = Label(
            text=f"[color=000000]📝 {self.example_count} examples[/color]",
            markup=True, font_size=24, halign='left', valign='middle'
        )
        footer.add_widget(example_label)
        
        # Click hint
        click_label = Label(
            text="[color=666666]Click for details[/color]",
            markup=True, font_size=20, size_hint_x=None, width=120,
            halign='right', valign='middle'
        )
        footer.add_widget(click_label)
        self.add_widget(footer)
    
    def _get_difficulty_color(self, difficulty: str) -> str:
        """Get color for difficulty"""
        colors = {
            "easy": "00AA00",      # Green
            "medium": "FF8800",    # Orange
            "hard": "FF0000"       # Red
        }
        return colors.get(difficulty, "FF8800")
    
    def on_press(self):
        """Handle card press"""
        if self.on_press_callback:
            self.on_press_callback()


class VocabExpressionCard(BaseCard):
    """Vocabulary expression card"""
    
    vocab_name = StringProperty("")
    vocab_body = StringProperty("")
    explanation = StringProperty("")
    example_count = NumericProperty(0)
    difficulty = StringProperty("medium")
    
    def __init__(self, vocab_data: dict, on_press_callback=None, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=10, 
                        size_hint_y=None, height=200, **kwargs)
        
        self.vocab_name = vocab_data.get("name", "")
        self.vocab_body = vocab_data.get("body", "")
        self.explanation = vocab_data.get("explanation", "")
        self.example_count = vocab_data.get("example_count", 0)
        self.difficulty = vocab_data.get("difficulty", "medium")
        self.on_press_callback = on_press_callback
        
        self._build_ui()
    
    def _build_ui(self):
        """Build UI"""
        # Header: title and difficulty
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        # Title
        title_label = Label(
            text=f"[b][color=000000]{self.vocab_name}[/color][/b]",
            markup=True, font_size=32, halign='left', valign='middle',
            size_hint_x=0.7
        )
        header.add_widget(title_label)
        
        # Difficulty label
        difficulty_color = self._get_difficulty_color(self.difficulty)
        difficulty_label = Label(
            text=f"[color={difficulty_color}]{self.difficulty.upper()}[/color]",
            markup=True, font_size=24, size_hint_x=0.3,
            halign='right', valign='middle'
        )
        header.add_widget(difficulty_label)
        self.add_widget(header)
        
        # Vocabulary body
        body_label = Label(
            text=f"[color=000000]{self.vocab_body}[/color]",
            markup=True, font_size=28, halign='left', valign='top',
            size_hint_y=None, height=40
        )
        self.add_widget(body_label)
        
        # Explanation
        explanation_label = Label(
            text=f"[color=000000]{self.explanation[:80]}{'...' if len(self.explanation) > 80 else ''}[/color]",
            markup=True, font_size=24, halign='left', valign='top',
            size_hint_y=None, height=60, text_size=(self.width - 30, None)
        )
        self.add_widget(explanation_label)
        
        # Footer: example count and click hint
        footer = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        
        # Example count
        example_label = Label(
            text=f"[color=000000]📝 {self.example_count} examples[/color]",
            markup=True, font_size=24, halign='left', valign='middle'
        )
        footer.add_widget(example_label)
        
        # Click hint
        click_label = Label(
            text="[color=666666]Click for details[/color]",
            markup=True, font_size=20, size_hint_x=None, width=120,
            halign='right', valign='middle'
        )
        footer.add_widget(click_label)
        self.add_widget(footer)
    
    def _get_difficulty_color(self, difficulty: str) -> str:
        """Get color for difficulty"""
        colors = {
            "easy": "00AA00",      # Green
            "medium": "FF8800",    # Orange
            "hard": "FF0000"       # Red
        }
        return colors.get(difficulty, "FF8800")
    
    def on_press(self):
        """Handle card press"""
        if self.on_press_callback:
            self.on_press_callback()


class CategoryFilterButton(ButtonBehavior, BoxLayout):
    """Category filter button"""
    
    def __init__(self, text: str, category: str, is_selected: bool = False, 
                 on_press_callback=None, **kwargs):
        super().__init__(orientation='horizontal', padding=10, spacing=5, 
                        size_hint_y=None, height=50, **kwargs)
        
        self.category = category
        self.is_selected = is_selected
        self.on_press_callback = on_press_callback
        
        self._build_ui(text)
    
    def _build_ui(self, text: str):
        """Build UI"""
        # Add border and background
        with self.canvas.before:
            # Black border
            Color(0, 0, 0, 1)
            self.border_rect = RoundedRectangle(radius=[10], pos=self.pos, size=self.size)
            # White background
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[8], pos=(self.x+2, self.y+2), size=(self.width-4, self.height-4))
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Text label
        self.text_label = Label(
            text=f"[color=000000]{text}[/color]",
            markup=True, font_size=24, halign='center', valign='middle'
        )
        self.add_widget(self.text_label)
        
        # Update selection state
        self.set_selected(self.is_selected)
    
    def _update_rect(self, *args):
        """Update border and background position"""
        self.border_rect.pos = self.pos
        self.border_rect.size = self.size
        self.bg_rect.pos = (self.x+2, self.y+2)
        self.bg_rect.size = (self.width-4, self.height-4)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        
        # Clear canvas and redraw
        self.canvas.before.clear()
        
        with self.canvas.before:
            # Black border
            Color(0, 0, 0, 1)
            self.border_rect = RoundedRectangle(radius=[10], pos=self.pos, size=self.size)
            
            # Background color based on selection
            if selected:
                Color(0.2, 0.6, 1, 1)  # Blue background
            else:
                Color(1, 1, 1, 1)  # White background
            self.bg_rect = RoundedRectangle(radius=[8], pos=(self.x+2, self.y+2), size=(self.width-4, self.height-4))
        
        # Update text color
        if selected:
            self.text_label.text = f"[color=FFFFFF]{self.text_label.text.split(']', 1)[1][:-8]}[/color]"
        else:
            self.text_label.text = f"[color=000000]{self.text_label.text.split(']', 1)[1][:-8]}[/color]"
    
    def on_press(self):
        """Handle button press"""
        if self.on_press_callback:
            self.on_press_callback(self.category)


class SearchBox(BoxLayout):
    """Search box component"""
    
    def __init__(self, on_text_change=None, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=60, 
                        spacing=10, padding=10, **kwargs)
        
        self.on_text_change = on_text_change
        
        # Add border and background
        with self.canvas.before:
            # Black border
            Color(0, 0, 0, 1)
            self.border_rect = RoundedRectangle(radius=[10], pos=self.pos, size=self.size)
            # White background
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[8], pos=(self.x+2, self.y+2), size=(self.width-4, self.height-4))
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Search icon
        search_icon = Label(
            text="🔍",
            font_size=24, size_hint_x=None, width=40,
            halign='center', valign='middle'
        )
        self.add_widget(search_icon)
        
        # Search input
        from kivy.uix.textinput import TextInput
        self.search_input = TextInput(
            hint_text="Search grammar rules...",
            font_size=24, multiline=False,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1)
        )
        self.search_input.bind(text=self._on_text_change)
        self.add_widget(self.search_input)
    
    def _update_rect(self, *args):
        """Update border and background position"""
        self.border_rect.pos = self.pos
        self.border_rect.size = self.size
        self.bg_rect.pos = (self.x+2, self.y+2)
        self.bg_rect.size = (self.width-4, self.height-4)
    
    def _on_text_change(self, instance, value):
        """Handle text change"""
        if self.on_text_change:
            self.on_text_change(value)
    
    def get_text(self) -> str:
        """Get search text"""
        return self.search_input.text
    
    def clear_text(self):
        """Clear search text"""
        self.search_input.text = "" 