#!/usr/bin/env python3
"""
测试TextInputWithChatApp集成到主程序
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from screens.main_screen import MainScreen
from screens.text_input_chat_screen import TextInputChatScreen

class TestTextInputChatIntegrationApp(App):
    """测试TextInputWithChatApp集成应用"""
    
    def build(self):
        """构建测试应用"""
        sm = ScreenManager(transition=NoTransition())
        
        # 添加主屏幕
        main_screen = MainScreen(name="main")
        sm.add_widget(main_screen)
        
        # 添加text_input_chat屏幕
        textinput_chat_screen = TextInputChatScreen(name="textinput_chat")
        sm.add_widget(textinput_chat_screen)
        
        return sm

if __name__ == '__main__':
    print("🧪 测试TextInputWithChatApp集成...")
    print("📱 启动测试应用...")
    print("📋 点击任意文章卡片应该跳转到text_input_chat页面")
    print("💬 页面包含文章阅读和AI聊天功能")
    print("⬅️ 点击左上角返回按钮应该回到主页面")
    print("-" * 50)
    
    TestTextInputChatIntegrationApp().run() 