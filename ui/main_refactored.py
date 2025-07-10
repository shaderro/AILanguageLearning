"""
重构后的主文件
展示如何使用新的模块化结构
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

# 导入重构后的组件
from components.cards import ClickableCard, VocabCard
from components.buttons import TabButton, SubTabButton
from components.modals import AIChatModal
from screens.main_screen import MainScreen
from screens.article_screen import ArticleScreen
from utils.swipe_handler import SwipeHandler


class LangUIAppRefactored(App):
    """重构后的语言学习应用"""
    
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
    LangUIAppRefactored().run() 