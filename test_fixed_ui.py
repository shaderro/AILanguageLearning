#!/usr/bin/env python3
"""
测试修复后的UI效果
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest

class FixedUITestApp(App):
    """测试修复后的UI效果"""
    
    def build(self):
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加测试聊天屏幕
        test_chat_screen = TextInputChatScreenTest(name='test_chat')
        sm.add_widget(test_chat_screen)
        
        # 运行测试功能
        test_chat_screen.test_run()
        
        print("\n🎯 修复后的UI测试说明:")
        print("1. 使用测试版本的聊天界面，文本渲染正常")
        print("2. 文章内容使用token化显示，每个词/短语独立")
        print("3. 字号已放大到48px，便于阅读")
        print("4. 支持文本选择和AI聊天功能")
        print("5. 异步处理，UI响应流畅")
        print("6. 测试操作:")
        print("   - 点击文章中的词/短语进行选择")
        print("   - 在聊天框输入问题")
        print("   - 观察文本渲染是否正常")
        print("   - 验证AI回复功能")
        
        return sm

def main():
    """主函数"""
    print("🚀 启动修复后的UI测试...")
    print("📱 将打开GUI窗口，请测试以下功能:")
    print("   ✅ 文本渲染正常（无堆叠）")
    print("   ✅ 字符显示正确（无损坏）")
    print("   ✅ 文本选择功能")
    print("   ✅ AI聊天功能")
    print("   ✅ 异步处理")
    print("   ✅ UI响应性")
    
    # 设置窗口大小
    Window.size = (1400, 900)
    
    # 运行应用
    app = FixedUITestApp()
    app.run()

if __name__ == "__main__":
    main() 