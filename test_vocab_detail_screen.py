#!/usr/bin/env python3
"""
测试词汇详情页面
验证词汇详情页面的显示和导航功能
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

# 导入词汇详情页面
from ui.screens.vocab_detail_screen import VocabDetailScreen

class TestVocabDetailApp(App):
    """测试词汇详情页面的应用"""
    
    def build(self):
        """构建应用"""
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 创建测试数据
        test_vocab_data = {
            'vocab_id': 1,
            'vocab_body': 'in which',
            'explanation': '用于引导定语从句的介词短语，表示"在其中"或"在...中"',
            'examples': [
                {
                    'text_id': 1,
                    'sentence_id': 1,
                    'context_explanation': '```json\n{"explanation": "在这个句子中，\'in which\' 用来引导定语从句，修饰前面的名词，表示在某种情况或条件下。"}\n```'
                }
            ]
        }
        
        # 创建词汇详情页面
        vocab_detail_screen = VocabDetailScreen(vocab_data=test_vocab_data)
        vocab_detail_screen.name = 'vocab_detail_screen'
        
        # 创建测试主页面
        test_screen = Screen(name='test_screen')
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 添加标题
        title_label = Label(
            text='词汇详情页面测试',
            font_size=24,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(title_label)
        
        # 添加说明
        desc_label = Label(
            text='点击下面的按钮查看词汇详情页面',
            font_size=16,
            size_hint_y=None,
            height=30
        )
        layout.add_widget(desc_label)
        
        # 添加测试按钮
        test_btn = Button(
            text='查看词汇详情',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 1, 1)
        )
        test_btn.bind(on_press=lambda x: setattr(sm, 'current', 'vocab_detail_screen'))
        layout.add_widget(test_btn)
        
        # 添加空白区域
        layout.add_widget(Label())
        
        test_screen.add_widget(layout)
        
        # 创建Learn屏幕（用于返回按钮）
        learn_screen = Screen(name='learn_screen')
        learn_layout = BoxLayout(orientation='vertical', padding=20)
        learn_label = Label(text='Learn Screen', font_size=24)
        learn_layout.add_widget(learn_label)
        learn_screen.add_widget(learn_layout)
        
        # 创建Main屏幕（用于底部导航）
        main_screen = Screen(name='main')
        main_layout = BoxLayout(orientation='vertical', padding=20)
        main_label = Label(text='Main Screen', font_size=24)
        main_layout.add_widget(main_label)
        main_screen.add_widget(main_layout)
        
        # 添加屏幕到管理器
        sm.add_widget(test_screen)
        sm.add_widget(vocab_detail_screen)
        sm.add_widget(learn_screen)
        sm.add_widget(main_screen)
        
        return sm

def main():
    """主函数"""
    print("🧪 开始测试词汇详情页面...")
    print("=" * 50)
    print("📋 测试内容:")
    print("   ✅ 词汇详情页面显示")
    print("   ✅ 词汇数据加载")
    print("   ✅ 示例句子显示")
    print("   ✅ 示例解释显示")
    print("   ✅ 底部导航功能")
    print("   ✅ 返回按钮功能")
    print("=" * 50)
    
    try:
        app = TestVocabDetailApp()
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