#!/usr/bin/env python3
"""
测试主程序集成功能
验证点击文章卡片是否能正确跳转到text_input_chat页面
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from screens.main_screen import MainScreen
from screens.text_input_chat_screen import TextInputChatScreen
from screens.vocab_detail_screen import VocabDetailScreen
from screens.grammar_detail_screen import GrammarDetailScreen

class TestMainIntegrationApp(App):
    """测试主程序集成应用"""
    
    def build(self):
        """构建测试应用"""
        sm = ScreenManager(transition=NoTransition())
        
        # 添加主屏幕
        main_screen = MainScreen(name="main")
        sm.add_widget(main_screen)
        
        # 添加text_input_chat屏幕
        textinput_chat_screen = TextInputChatScreen(name="textinput_chat")
        sm.add_widget(textinput_chat_screen)
        
        # 添加其他必要的屏幕
        vocab_detail_screen = VocabDetailScreen(name="vocab_detail")
        sm.add_widget(vocab_detail_screen)
        grammar_detail_screen = GrammarDetailScreen(name="grammar_detail")
        sm.add_widget(grammar_detail_screen)
        
        return sm

if __name__ == '__main__':
    print("🧪 测试主程序集成功能...")
    print("📱 启动主程序测试应用...")
    print("📋 点击任意文章卡片应该跳转到text_input_chat页面")
    print("⬅️ 点击左上角返回按钮应该回到主页面")
    print("💬 在text_input_chat页面可以:")
    print("   - 选择文章中的文本")
    print("   - 在聊天框中输入问题")
    print("   - 与AI助手对话")
    print("-" * 50)
    
    TestMainIntegrationApp().run() 