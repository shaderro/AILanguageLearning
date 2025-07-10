"""
主应用文件
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from .screens.main_screen import MainScreen


class LangUIApp(App):
    """语言学习应用主类"""
    
    def build(self):
        """构建应用界面"""
        sm = ScreenManager()
        main_screen = MainScreen(sm, name="main")
        sm.add_widget(main_screen)
        return sm


if __name__ == '__main__':
    LangUIApp().run() 