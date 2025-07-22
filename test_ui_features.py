"""
UI功能测试脚本
测试字号放大和文本保持功能
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest

class UIFeaturesTestApp(App):
    """UI功能测试应用"""
    
    def build(self):
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加测试聊天屏幕
        test_chat_screen = TextInputChatScreenTest(name='test_chat')
        sm.add_widget(test_chat_screen)
        
        # 运行测试功能
        test_chat_screen.test_run()
        
        print("\n🎯 UI功能测试说明:")
        print("1. 文章内容字号已放大到48px (原来的3倍)")
        print("2. 选中文本显示字号已放大到42px (原来的3倍)")
        print("3. 点击输入框时，之前选择的文本会被保持")
        print("4. 可以测试以下操作:")
        print("   - 在文章中选择文本")
        print("   - 点击输入框")
        print("   - 输入问题并发送")
        print("   - 验证选中文本是否被保持")
        
        return sm

def main():
    """主函数"""
    print("🚀 启动UI功能测试...")
    print("📱 将打开GUI窗口，请测试以下功能:")
    print("   ✅ 文章内容字号放大")
    print("   ✅ 选中文本显示字号放大")
    print("   ✅ 输入框焦点时保持文本选择")
    
    # 设置窗口大小
    Window.size = (1400, 900)
    
    # 运行应用
    app = UIFeaturesTestApp()
    app.run()

if __name__ == "__main__":
    main() 