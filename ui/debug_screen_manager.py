#!/usr/bin/env python3
"""
调试ScreenManager和TextInputChatScreen的注册问题
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from screens.main_screen import MainScreen
from screens.text_input_chat_screen import TextInputChatScreen

class DebugApp(App):
    """调试应用"""
    
    def build(self):
        """构建调试应用"""
        print("开始构建ScreenManager...")
        
        sm = ScreenManager(transition=NoTransition())
        
        print("添加MainScreen...")
        main_screen = MainScreen(name="main")
        sm.add_widget(main_screen)
        
        print("添加TextInputChatScreen...")
        textinput_chat_screen = TextInputChatScreen(name="textinput_chat")
        sm.add_widget(textinput_chat_screen)
        
        print("ScreenManager构建完成")
        print(f"当前屏幕数量: {len(sm.screens)}")
        print(f"屏幕名称列表: {[screen.name for screen in sm.screens]}")
        
        return sm

if __name__ == '__main__':
    print("🧪 调试ScreenManager注册...")
    print("-" * 50)
    
    DebugApp().run() 