#!/usr/bin/env python3
"""
语言学习应用 - 主启动文件
重构后的模块化应用入口
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

# 导入重构后的组件
from screens.main_screen import MainScreen
from screens.reading_content_screen import ReadingContentScreen
from screens.read_content_screen import ReadContentScreen


class LangUIApp(App):
    """语言学习应用主类"""
    
    def build(self):
        """构建应用界面"""
        sm = ScreenManager()
        
        # 创建主屏幕 - 传递屏幕管理器
        main_screen = MainScreen(name="main")
        sm.add_widget(main_screen)
        
        # 注册文章内容屏幕
        read_screen = ReadContentScreen(name="read")
        sm.add_widget(read_screen)
        
        return sm


if __name__ == '__main__':
    print("🚀 启动语言学习应用...")
    print("📁 当前工作目录:", os.getcwd())
    print("🐍 Python版本:", sys.version.split()[0])
    print("📦 使用重构后的模块化结构")
    print("-" * 50)
    LangUIApp().run() 