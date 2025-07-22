"""
Button components module
Contains various custom button components
"""

from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Line, Rectangle


class BorderedButton(Button):
    """Button with border"""
    
    def __init__(self, border_width=1, **kwargs):
        super().__init__(**kwargs)
        self.border_width = border_width
        self._setup_border()
    
    def _setup_border(self):
        """Setup button border"""
        with self.canvas.before:
            Color(0, 0, 0, 1)  # Black border
            self._border = Line(
                rectangle=(self.x, self.y, self.width, self.height), 
                width=self.border_width
            )
        
        self.bind(pos=self._update_border, size=self._update_border)
    
    def _update_border(self, instance, value):
        """Update border position"""
        if hasattr(self, '_border'):
            self._border.rectangle = (instance.x, instance.y, instance.width, instance.height)


class TabButton(Button):
    """Tab button with consistent border"""
    
    def __init__(self, text, is_active=False, **kwargs):
        # Extract border_width from kwargs before passing to Button
        border_width = kwargs.pop('border_width', 2)
        
        # Set default styles
        default_kwargs = {
            'background_normal': '',
            'background_color': (0.2, 0.6, 1, 1) if is_active else (0.8, 0.8, 0.8, 1),
            'color': (1, 1, 1, 1) if is_active else (0, 0, 0, 1),
            'font_size': 24,
            'size_hint_x': 0.5
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)
        self.is_active = is_active
        self.border_width = border_width
        self._setup_border()
    
    def _setup_border(self):
        """Setup button border using Rectangle for consistency"""
        with self.canvas.before:
            # Background rectangle (fills the entire button)
            Color(*self.background_color)
            self._background = Rectangle(
                pos=(self.x, self.y), 
                size=(self.width, self.height)
            )
            # Border rectangle (drawn on top)
            Color(0, 0, 0, 1)  # Black border
            self._border = Rectangle(
                pos=(self.x, self.y), 
                size=(self.width, self.height)
            )
        
        self.bind(pos=self._update_border, size=self._update_border)
    
    def _update_border(self, instance, value):
        """Update border and background position"""
        if hasattr(self, '_border') and hasattr(self, '_background'):
            self._border.pos = (instance.x, instance.y)
            self._border.size = (instance.width, instance.height)
            self._background.pos = (instance.x, instance.y)
            self._background.size = (instance.width, instance.height)
    
    def set_active(self, active):
        """Set button active state"""
        self.is_active = active
        if active:
            self.background_color = (0.2, 0.6, 1, 1)  # Blue
            self.color = (1, 1, 1, 1)  # White text
        else:
            self.background_color = (0.8, 0.8, 0.8, 1)  # Gray
            self.color = (0, 0, 0, 1)  # Black text
        
        # Update background color
        if hasattr(self, '_background'):
            # Clear and redraw background
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*self.background_color)
                self._background = Rectangle(
                    pos=(self.x, self.y), 
                    size=(self.width, self.height)
                )
                # Redraw border
                Color(0, 0, 0, 1)  # Black border
                self._border = Rectangle(
                    pos=(self.x, self.y), 
                    size=(self.width, self.height)
                )


class SubTabButton(TabButton):
    """Sub tab button"""
    
    def __init__(self, text, is_active=False, **kwargs):
        default_kwargs = {
            'font_size': 20,
            'border_width': 1
        }
        default_kwargs.update(kwargs)
        super().__init__(text, is_active, **default_kwargs)


class BottomTabBar(BoxLayout):
    """Unified bottom tab bar component"""
    
    def __init__(self, read_callback=None, learn_callback=None, active_tab="read", **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=60, 
                        spacing=10, padding=(20, 0, 20, 0), **kwargs)
        
        self.read_callback = read_callback
        self.learn_callback = learn_callback
        
        # Setup border
        self._setup_border()
        
        # Create tab buttons
        self.read_tab = TabButton('Read', is_active=(active_tab == "read"))
        self.learn_tab = TabButton('Learn', is_active=(active_tab == "learn"))
        
        # Bind events
        self.read_tab.bind(on_release=self._on_read_press)
        self.learn_tab.bind(on_release=self._on_learn_press)
        
        # Add buttons
        self.add_widget(self.read_tab)
        self.add_widget(self.learn_tab)
    
    def _setup_border(self):
        """Setup tab bar border"""
        with self.canvas.before:
            Color(0, 0, 0, 1)  # Black border
            self.border_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_border, size=self._update_border)
    
    def _update_border(self, *args):
        """Update border position"""
        if hasattr(self, 'border_rect'):
            self.border_rect.pos = self.pos
            self.border_rect.size = self.size
    
    def _on_read_press(self, instance):
        """Handle Read tab press"""
        self.set_active_tab("read")
        if self.read_callback:
            self.read_callback()
    
    def _on_learn_press(self, instance):
        """Handle Learn tab press"""
        self.set_active_tab("learn")
        if self.learn_callback:
            self.learn_callback()
    
    def set_active_tab(self, tab_name):
        """Set active tab"""
        if tab_name == "read":
            self.read_tab.set_active(True)
            self.learn_tab.set_active(False)
        elif tab_name == "learn":
            self.read_tab.set_active(False)
            self.learn_tab.set_active(True) 