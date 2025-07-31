#!/usr/bin/env python3
"""
测试真实数据绑定功能
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from ui.screens.main_screen import MainScreen

class RealDataBindingTestApp(App):
    """测试真实数据绑定的应用"""
    
    def build(self):
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加主屏幕
        main_screen = MainScreen(name='main')
        sm.add_widget(main_screen)
        
        print("\n🎯 真实数据绑定测试说明:")
        print("1. 主屏幕已加载真实的语法和词汇数据")
        print("2. 点击'Learn'标签页查看语法和词汇卡片")
        print("3. 语法卡片显示真实的语法规则和例句")
        print("4. 词汇卡片显示真实的词汇和解释")
        print("5. 测试操作:")
        print("   - 点击'Learn'标签页")
        print("   - 点击'Grammar'子标签查看语法规则")
        print("   - 点击'Vocabulary'子标签查看词汇")
        print("   - 点击卡片查看详细信息")
        print("   - 验证数据是否来自真实文件")
        
        return sm

def main():
    """主函数"""
    print("🚀 启动真实数据绑定测试...")
    print("📱 将打开GUI窗口，请测试以下功能:")
    print("   ✅ 真实语法数据加载")
    print("   ✅ 真实词汇数据加载")
    print("   ✅ 语法卡片显示")
    print("   ✅ 词汇卡片显示")
    print("   ✅ 卡片点击功能")
    print("   ✅ 数据来源验证")
    
    # 设置窗口大小
    Window.size = (1400, 900)
    
    # 运行应用
    app = RealDataBindingTestApp()
    app.run()

if __name__ == "__main__":
    main() 