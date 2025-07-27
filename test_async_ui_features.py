"""
异步UI功能测试脚本
测试异步执行MainAssistant功能，包含完整的文字选择功能
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from ui.screens.text_input_chat_screen_async import AsyncTextInputChatScreen

class AsyncUIFeaturesTestApp(App):
    """异步UI功能测试应用"""
    
    def build(self):
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加异步聊天屏幕
        async_chat_screen = AsyncTextInputChatScreen(name='async_chat')
        sm.add_widget(async_chat_screen)
        
        # 运行测试功能
        async_chat_screen.test_run()
        
        print("\n🎯 异步UI功能测试说明:")
        print("1. 文章内容字号已放大到48px")
        print("2. 文字选择功能完整支持:")
        print("   - 点击选择单个词/短语")
        print("   - 拖拽选择多个词/短语")
        print("   - 连续点击添加选择")
        print("   - 跨句子选择限制")
        print("3. 聊天界面支持异步处理:")
        print("   - 发送消息后UI不会卡顿")
        print("   - 实时显示处理状态")
        print("   - 后台处理MainAssistant")
        print("4. 可以测试以下操作:")
        print("   - 在文章中选择文本")
        print("   - 发送问题")
        print("   - 观察UI响应性")
        print("   - 查看异步处理状态")
        print("5. 异步处理流程:")
        print("   - 发送消息 → UI置灰")
        print("   - 后台处理MainAssistant")
        print("   - 显示AI回复 → UI恢复")
        print("   - 后台继续处理语法/词汇")
        
        return sm

def main():
    """主函数"""
    print("🚀 启动异步UI功能测试...")
    print("📱 将打开GUI窗口，请测试以下功能:")
    print("   ✅ 完整的文字选择功能")
    print("   ✅ 异步MainAssistant处理")
    print("   ✅ UI响应性保持")
    print("   ✅ 后台任务处理")
    print("   ✅ 状态显示更新")
    
    # 设置窗口大小
    Window.size = (1400, 900)
    
    # 运行应用
    app = AsyncUIFeaturesTestApp()
    app.run()

if __name__ == "__main__":
    main() 