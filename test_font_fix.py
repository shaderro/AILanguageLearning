#!/usr/bin/env python3
"""
测试字体修复
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from ui.utils.font_utils import FontUtils

class FontTestApp(App):
    """测试字体的应用"""
    
    def build(self):
        # 测试字体工具类
        print("🔤 测试字体工具类...")
        font_name = FontUtils.get_font_name()
        print(f"   字体名称: {font_name}")
        
        # 创建主布局
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 测试普通Label
        normal_label = Label(
            text="普通Label测试 - Normal Label Test",
            font_size=24,
            halign='center'
        )
        layout.add_widget(normal_label)
        
        # 测试中文字体Label
        chinese_label = FontUtils.create_label_with_chinese_support(
            text="中文字体Label测试 - Chinese Font Label Test",
            font_size=24,
            halign='center'
        )
        layout.add_widget(chinese_label)
        
        # 测试中文内容
        chinese_content = FontUtils.create_label_with_chinese_support(
            text="副词currently的用法 - 这是一个中文语法规则",
            font_size=20,
            halign='center'
        )
        layout.add_widget(chinese_content)
        
        # 测试英文内容
        english_content = FontUtils.create_label_with_chinese_support(
            text="in which - This is an English vocabulary expression",
            font_size=20,
            halign='center'
        )
        layout.add_widget(english_content)
        
        print("\n🎯 字体测试说明:")
        print("1. 应该显示4行文本")
        print("2. 中文和英文都应该正确显示")
        print("3. 没有乱码字符")
        
        return layout

def main():
    """主函数"""
    print("🚀 启动字体测试...")
    print("📱 将打开GUI窗口，请测试以下功能:")
    print("   ✅ 中文字体支持")
    print("   ✅ 英文显示正常")
    print("   ✅ 中文显示正常")
    print("   ✅ 无乱码字符")
    
    # 设置窗口大小
    Window.size = (800, 600)
    
    # 运行应用
    app = FontTestApp()
    app.run()

if __name__ == "__main__":
    main() 