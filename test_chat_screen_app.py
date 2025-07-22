"""
测试聊天屏幕应用
用于测试TextInputChatScreenTest页面
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

# 导入测试屏幕
from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest

class TestChatScreenApp(App):
    """测试聊天屏幕应用"""
    
    def build(self):
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加测试聊天屏幕
        test_chat_screen = TextInputChatScreenTest(name='test_chat')
        sm.add_widget(test_chat_screen)
        
        # 运行测试功能
        test_chat_screen.test_run()
        
        return sm

if __name__ == '__main__':
    # 设置窗口大小
    Window.size = (1200, 800)
    app = TestChatScreenApp()
    app.run() 