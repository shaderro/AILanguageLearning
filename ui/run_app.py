#!/usr/bin/env python3
"""
启动脚本 - 正确运行重构后的应用
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
from screens.article_screen import ArticleScreen


class LangUIApp(App):
    """语言学习应用主类"""
    
    def build(self):
        """构建应用界面"""
        sm = ScreenManager()
        
        # 创建主屏幕
        main_screen = MainScreen(sm, name="main")
        sm.add_widget(main_screen)
        
        # 创建文章屏幕
        article_screen = ArticleScreen(name="article")
        sm.add_widget(article_screen)
        
        return sm


if __name__ == '__main__':
    print("启动语言学习应用...")
    print("当前工作目录:", os.getcwd())
    print("Python路径:", sys.path[:3])  # 只显示前3个路径
    LangUIApp().run() 