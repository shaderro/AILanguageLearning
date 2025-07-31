#!/usr/bin/env python3
"""
测试facilitate词汇详情页面
验证explanation数据解析和UI布局
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

class TestFacilitateVocabApp(App):
    """测试facilitate词汇详情页面的应用"""
    
    def build(self):
        """构建应用"""
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 创建facilitate词汇的测试数据
        facilitate_vocab_data = {
            'vocab_id': 13,
            'vocab_body': 'facilitate',
            'explanation': "{'explanation': \"The word 'facilitate' is a verb that means to make an action or process easier or more efficient. In the given sentence, it is used to describe how the internet helps or enables collaborative learning by providing platforms like online communities and language exchange programs. It implies that the internet acts as a tool or medium that supports and simplifies the process of learning together. The word is often used in contexts where something or someone helps to bring about a desired outcome with less effort or difficulty.\"}",
            'examples': [
                {
                    'text_id': 5,
                    'sentence_id': 7,
                    'context_explanation': '```json\n{"explanation": "在这句话中，\'facilitate\' 的意思是互联网使协作学习变得更容易或更顺畅，通过在线社区和语言交换项目来实现。"}\n```'
                }
            ]
        }
        
        # 创建词汇详情页面
        vocab_detail_screen = VocabDetailScreen(vocab_data=facilitate_vocab_data)
        vocab_detail_screen.name = 'vocab_detail_screen'
        
        # 创建测试主页面
        test_screen = Screen(name='test_screen')
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 添加标题
        title_label = Label(
            text='Facilitate词汇详情页面测试',
            font_size=24,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(title_label)
        
        # 添加说明
        desc_label = Label(
            text='点击下面的按钮查看facilitate词汇详情页面\n验证explanation数据解析和UI布局',
            font_size=16,
            size_hint_y=None,
            height=60
        )
        layout.add_widget(desc_label)
        
        # 添加测试按钮
        test_btn = Button(
            text='查看Facilitate词汇详情',
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
    print("🧪 开始测试facilitate词汇详情页面...")
    print("=" * 60)
    print("📋 测试内容:")
    print("   ✅ facilitate词汇数据解析")
    print("   ✅ explanation字段正确显示")
    print("   ✅ UI布局不堆叠")
    print("   ✅ 动态高度调整")
    print("   ✅ 示例解释正确显示")
    print("=" * 60)
    
    try:
        app = TestFacilitateVocabApp()
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