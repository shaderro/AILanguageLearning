#!/usr/bin/env python3
"""
语言学习应用 - 主启动文件
重构后的模块化应用入口
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition

# 导入重构后的组件
from screens.main_screen import MainScreen
from screens.reading_content_screen import ReadingContentScreen
from screens.vocab_detail_screen import VocabDetailScreen
from screens.grammar_detail_screen import GrammarDetailScreen
from screens.reading_content_textinput_screen import ReadingContentTextInputScreen
from screens.text_input_chat_screen import TextInputChatScreen
# from screens.read_content_screen import ReadContentScreen

class LangUIApp(App):
    """语言学习应用主类"""
    
    def build(self):
        """构建应用界面"""
        sm = ScreenManager(transition=NoTransition())
        main_screen = MainScreen(name="main")
        sm.add_widget(main_screen)
        read_screen = ReadingContentScreen(name="read")
        sm.add_widget(read_screen)
        textinput_screen = ReadingContentTextInputScreen(name="textinput_read")
        sm.add_widget(textinput_screen)
        textinput_chat_screen = TextInputChatScreen(name="textinput_chat")
        sm.add_widget(textinput_chat_screen)
        vocab_detail_screen = VocabDetailScreen(name="vocab_detail")
        sm.add_widget(vocab_detail_screen)
        grammar_detail_screen = GrammarDetailScreen(name="grammar_detail")
        sm.add_widget(grammar_detail_screen)
        return sm

if __name__ == '__main__':
    import os, sys
    print("🚀 启动语言学习应用...")
    print("📁 当前工作目录:", os.getcwd())
    print("🐍 Python版本:", sys.version.split()[0])
    print("📦 使用重构后的模块化结构")
    print("-" * 50)
    LangUIApp().run()