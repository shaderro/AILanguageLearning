#!/usr/bin/env python3
"""
测试text_input_ai_chat集成到主程序
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from screens.main_screen import MainScreen
from screens.reading_content_textinput_screen import ReadingContentTextInputScreen

class TestIntegrationApp(App):
    """测试集成应用"""
    
    def build(self):
        """构建测试应用"""
        sm = ScreenManager(transition=NoTransition())
        
        # 添加主屏幕
        main_screen = MainScreen(name="main")
        sm.add_widget(main_screen)
        
        # 添加text_input屏幕
        textinput_screen = ReadingContentTextInputScreen(name="textinput_read")
        sm.add_widget(textinput_screen)
        
        return sm

if __name__ == '__main__':
    print("🧪 测试text_input_ai_chat集成...")
    print("📱 启动测试应用...")
    print("📋 点击任意文章卡片应该跳转到text_input页面")
    print("⬅️ 点击左上角返回按钮应该回到主页面")
    print("-" * 50)
    
    TestIntegrationApp().run() 