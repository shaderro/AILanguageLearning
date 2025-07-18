"""
文本输入聊天应用主文件
使用模块化的屏幕结构
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

# 导入模块化的屏幕
from ui.screens.text_input_chat_screen import TextInputChatScreen

class TextInputChatApp(App):
    """文本输入聊天应用"""
    
    def build(self):
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加文本输入聊天屏幕
        chat_screen = TextInputChatScreen(name='textinput_chat')
        sm.add_widget(chat_screen)
        
        return sm

if __name__ == '__main__':
    # 设置窗口大小
    Window.size = (1200, 800)
    app = TextInputChatApp()
    app.run() 