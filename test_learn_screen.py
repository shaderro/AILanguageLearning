#!/usr/bin/env python3
"""
测试Learn页面的数据加载
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from ui.screens.learn_screen import LearnScreen
from ui.services.language_learning_binding_service import LanguageLearningBindingService

class LearnScreenTestApp(App):
    """测试Learn页面的应用"""
    
    def build(self):
        # 创建数据绑定服务
        binding_service = LanguageLearningBindingService()
        
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加Learn页面
        learn_screen = LearnScreen(data_binding_service=binding_service, name='learn')
        sm.add_widget(learn_screen)
        
        # 添加一个虚拟的main页面以避免导航错误
        from kivy.uix.screenmanager import Screen
        from kivy.uix.label import Label
        
        class DummyMainScreen(Screen):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.name = "main"
                self.add_widget(Label(text="Dummy Main Screen"))
        
        dummy_main = DummyMainScreen()
        sm.add_widget(dummy_main)
        
        print("\n🎯 Learn页面测试说明:")
        print("1. Learn页面已加载，使用真实数据绑定服务")
        print("2. 应该显示语法规则和词汇表达式的卡片")
        print("3. 测试操作:")
        print("   - 查看语法规则卡片是否显示")
        print("   - 查看词汇表达式卡片是否显示")
        print("   - 点击卡片测试交互功能")
        print("   - 使用搜索框测试搜索功能")
        print("   - 使用分类按钮测试过滤功能")
        
        return sm

def main():
    """主函数"""
    print("🚀 启动Learn页面测试...")
    print("📱 将打开GUI窗口，请测试以下功能:")
    print("   ✅ 真实数据加载")
    print("   ✅ 语法规则卡片显示")
    print("   ✅ 词汇表达式卡片显示")
    print("   ✅ 卡片点击功能")
    print("   ✅ 搜索和过滤功能")
    
    # 设置窗口大小
    Window.size = (1400, 900)
    
    # 运行应用
    app = LearnScreenTestApp()
    app.run()

if __name__ == "__main__":
    main() 