#!/usr/bin/env python3
"""
测试Learn页面按钮点击问题
重现从Vocabulary切换到Grammar时按钮无法点击的问题
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
from kivy.clock import Clock

# 导入Learn页面
from ui.screens.learn_screen import LearnScreen
from ui.services.language_learning_binding_service import LanguageLearningBindingService

class TestButtonClickIssueApp(App):
    """测试按钮点击问题的应用"""
    
    def build(self):
        """构建应用"""
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 创建数据绑定服务
        data_binding_service = LanguageLearningBindingService()
        
        # 创建Learn页面
        self.learn_screen = LearnScreen(data_binding_service=data_binding_service)
        self.learn_screen.name = 'learn_screen'
        
        # 创建测试主页面
        test_screen = Screen(name='test_screen')
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 添加标题
        title_label = Label(
            text='按钮点击问题测试',
            font_size=24,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(title_label)
        
        # 添加说明
        desc_label = Label(
            text='点击进入Learn页面，然后测试Grammar和Vocabulary按钮的切换',
            font_size=16,
            size_hint_y=None,
            height=60
        )
        layout.add_widget(desc_label)
        
        # 添加测试按钮
        test_btn = Button(
            text='进入Learn页面测试',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 1, 1)
        )
        test_btn.bind(on_press=lambda x: setattr(sm, 'current', 'learn_screen'))
        layout.add_widget(test_btn)
        
        # 添加调试按钮
        debug_btn = Button(
            text='检查按钮状态',
            size_hint_y=None,
            height=50,
            background_color=(0.8, 0.4, 0.2, 1)
        )
        debug_btn.bind(on_press=self._check_button_status)
        layout.add_widget(debug_btn)
        
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
        sm.add_widget(self.learn_screen)
        sm.add_widget(main_screen)
        
        return sm
    
    def _check_button_status(self, instance):
        """检查按钮状态"""
        try:
            grammar_btn = self.learn_screen.grammar_button
            vocab_btn = self.learn_screen.vocab_button
            
            print("🔍 按钮状态检查:")
            print(f"Grammar按钮 - disabled: {grammar_btn.disabled}, opacity: {grammar_btn.opacity}")
            print(f"Vocabulary按钮 - disabled: {vocab_btn.disabled}, opacity: {vocab_btn.opacity}")
            
            # 检查父容器状态
            grammar_section = self.learn_screen.grammar_section
            vocab_section = self.learn_screen.vocab_section
            
            print(f"Grammar部分 - disabled: {grammar_section.disabled}, opacity: {grammar_section.opacity}")
            print(f"Vocabulary部分 - disabled: {vocab_section.disabled}, opacity: {vocab_section.opacity}")
            
        except Exception as e:
            print(f"❌ 检查按钮状态时出错: {e}")

def main():
    """主函数"""
    print("🧪 开始测试按钮点击问题...")
    print("=" * 60)
    print("📋 测试步骤:")
    print("   1. 进入Learn页面")
    print("   2. 点击Vocabulary按钮")
    print("   3. 尝试点击Grammar按钮")
    print("   4. 检查按钮是否可以正常切换")
    print("=" * 60)
    
    try:
        app = TestButtonClickIssueApp()
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