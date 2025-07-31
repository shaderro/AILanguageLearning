#!/usr/bin/env python3
"""
测试Learn页面的分类过滤功能
验证Grammar和Vocabulary的独立显示
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# 导入Learn页面
from ui.screens.learn_screen import LearnScreen
from ui.services.language_learning_binding_service import LanguageLearningBindingService

class TestLearnScreenFilterApp(App):
    """测试Learn页面分类过滤功能的应用"""
    
    def build(self):
        """构建应用"""
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 创建数据绑定服务
        data_binding_service = LanguageLearningBindingService()
        
        # 创建Learn页面
        learn_screen = LearnScreen(data_binding_service=data_binding_service)
        learn_screen.name = 'learn_screen'
        
        # 创建测试主页面
        test_screen = Screen(name='test_screen')
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 添加标题
        title_label = Label(
            text='Learn页面分类过滤测试',
            font_size=24,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(title_label)
        
        # 添加说明
        desc_label = Label(
            text='点击下面的按钮进入Learn页面\n验证Grammar和Vocabulary的独立显示',
            font_size=16,
            size_hint_y=None,
            height=60
        )
        layout.add_widget(desc_label)
        
        # 添加测试按钮
        test_btn = Button(
            text='进入Learn页面',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 1, 1)
        )
        test_btn.bind(on_press=lambda x: setattr(sm, 'current', 'learn_screen'))
        layout.add_widget(test_btn)
        
        # 添加空白区域
        layout.add_widget(Label())
        
        test_screen.add_widget(layout)
        
        # 创建Main屏幕（用于底部导航）
        main_screen = Screen(name='main')
        main_layout = BoxLayout(orientation='vertical', padding=20)
        main_label = Label(text='Main Screen', font_size=24)
        main_layout.add_widget(main_label)
        main_screen.add_widget(main_layout)
        
        # 添加屏幕到管理器
        sm.add_widget(test_screen)
        sm.add_widget(learn_screen)
        sm.add_widget(main_screen)
        
        return sm

def main():
    """主函数"""
    print("🧪 开始测试Learn页面分类过滤功能...")
    print("=" * 60)
    print("📋 测试内容:")
    print("   ✅ 去掉All选项")
    print("   ✅ 只显示Grammar和Vocabulary选项")
    print("   ✅ Grammar默认选中")
    print("   ✅ Grammar只显示语法规则")
    print("   ✅ Vocabulary只显示词汇表达式")
    print("   ✅ 切换功能正常")
    print("=" * 60)
    
    try:
        app = TestLearnScreenFilterApp()
        app.run()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("✅ 测试完成")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 