"""
Card components module
Contains various reusable card components
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle


class BaseCard(ButtonBehavior, BoxLayout):
    """Base card class, provides common border and background functionality"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_border()
    
    def _setup_border(self):
        """Setup card border and background"""
        with self.canvas.before:
            # Black border
            Color(0, 0, 0, 1)
            self.border_rect = RoundedRectangle(radius=[15], pos=self.pos, size=self.size)
            # White background
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[13], pos=(self.x+2, self.y+2), size=(self.width-4, self.height-4))
        
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        """Update border and background position"""
        self.border_rect.pos = self.pos
        self.border_rect.size = self.size
        self.bg_rect.pos = (self.x+2, self.y+2)
        self.bg_rect.size = (self.width-4, self.height-4)


class ClickableCard(BaseCard):
    """Clickable article card"""
    
    def __init__(self, title, words, level, percent, on_press_callback, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=10, 
                        size_hint_y=None, height=280, **kwargs)
        
        # Title and level
        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        top.add_widget(Label(
            text=f"[b][color=000000]{title}[/color][/b]", 
            markup=True, font_size=32, halign='left', valign='middle'
        ))
        top.add_widget(Label(
            text=f"[color=000000]{level}[/color]", 
            markup=True, font_size=24, size_hint_x=None, width=80, 
            halign='right', valign='middle'
        ))
        self.add_widget(top)
        
        # Word count
        self.add_widget(Label(
            text=f"[color=000000]{words} words[/color]", 
            markup=True, font_size=24, size_hint_y=None, height=50, halign='left'
        ))
        
        # Progress bar
        pb = ProgressBar(max=100, value=percent, height=30, size_hint_y=None)
        self.add_widget(pb)
        
        # Percentage and icon
        bottom = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        bottom.add_widget(Label(
            text=f"[color=000000]{percent}% read[/color]", 
            markup=True, font_size=24, halign='left'
        ))
        bottom.add_widget(Label(
            text="[color=000000]📖[/color]", 
            markup=True, font_size=32, size_hint_x=None, width=60, halign='right'
        ))
        self.add_widget(bottom)
        
        self.on_press_callback = on_press_callback
    
    def on_press(self):
        """Handle press event"""
        if self.on_press_callback:
            self.on_press_callback()


class VocabCard(BaseCard):
    """Vocabulary card"""
    
    def __init__(self, word, meaning, example, difficulty, on_press_callback=None, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=8, 
                        size_hint_y=None, height=120, **kwargs)
        
        self.on_press_callback = on_press_callback
        
        # Word and difficulty
        top_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        top_row.add_widget(Label(
            text=f"[b][color=000000]{word}[/color][/b]", 
            markup=True, font_size=28, halign='left', valign='middle'
        ))
        top_row.add_widget(Label(
            text=f"[color=000000]{difficulty}[/color]", 
            markup=True, font_size=20, size_hint_x=None, width=80, 
            halign='right', valign='middle'
        ))
        self.add_widget(top_row)
        
        # Meaning
        self.add_widget(Label(
            text=f"[color=000000]{meaning}[/color]", 
            markup=True, font_size=20, size_hint_y=None, height=40, halign='left'
        ))
        
        # Example
        self.add_widget(Label(
            text=f"[color=666666]{example}[/color]", 
            markup=True, font_size=18, size_hint_y=None, height=30, halign='left'
        ))
    
    def _get_difficulty_color(self, difficulty):
        """Get color for difficulty level"""
        colors = {
            "easy": "00AA00",      # Green
            "medium": "FF8800",    # Orange
            "hard": "FF0000"       # Red
        }
        return colors.get(difficulty.lower(), "FF8800")
    
    def on_press(self):
        """Handle press event"""
        if self.on_press_callback:
            self.on_press_callback() 