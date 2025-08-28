"""
数据绑定使用示例
展示如何连接ViewModel和数据服务
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

# 修复导入路径问题
import sys
import os
# 添加父目录到Python路径，以便导入viewmodels和services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入数据绑定组件
from viewmodels.text_input_chat_viewmodel import TextInputChatViewModel
from services.language_learning_binding_service import LanguageLearningBindingService
from screens.text_input_chat_screen import TextInputChatScreen

class DataBindingExampleApp(App):
    """数据绑定示例应用"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_binding_service = None
        self.viewmodel = None
    
    def build(self):
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 1. 创建数据绑定服务
        self._setup_data_binding()
        
        # 2. 创建ViewModel
        self._setup_viewmodel()
        
        # 3. 创建UI屏幕并绑定ViewModel
        self._setup_ui_screen(sm)
        
        # 4. 设置数据绑定
        self._setup_bindings()
        
        return sm
    
    def _setup_data_binding(self):
        """设置数据绑定服务"""
        # 使用语言学习特定的数据绑定服务
        self.data_binding_service = LanguageLearningBindingService()
        print("示例: 数据绑定服务已创建")
    
    def _setup_viewmodel(self):
        """设置ViewModel"""
        # 创建ViewModel并传入数据绑定服务
        self.viewmodel = TextInputChatViewModel(self.data_binding_service)
        
        # 注册ViewModel到数据绑定服务
        self.data_binding_service.register_viewmodel('text_input_chat', self.viewmodel)
        print("示例: ViewModel已创建并注册")
    
    def _setup_ui_screen(self, screen_manager):
        """设置UI屏幕"""
        # 创建聊天屏幕
        chat_screen = TextInputChatScreen(name='textinput_chat')
        
        # 将ViewModel传递给屏幕（需要在屏幕中添加ViewModel支持）
        # chat_screen.set_viewmodel(self.viewmodel)
        
        screen_manager.add_widget(chat_screen)
        print("示例: UI屏幕已创建")
    
    def _setup_bindings(self):
        """设置数据绑定"""
        # 绑定文章数据
        self.data_binding_service.bind_data_to_viewmodel(
            'article_title', 'text_input_chat', 'article_title'
        )
        self.data_binding_service.bind_data_to_viewmodel(
            'article_content', 'text_input_chat', 'article_content'
        )
        
        # 绑定聊天消息
        self.data_binding_service.bind_data_to_viewmodel(
            'chat_messages', 'text_input_chat', 'chat_messages'
        )
        
        print("示例: 数据绑定已设置")
    
    def demonstrate_data_binding(self):
        """演示数据绑定功能"""
        print("\n=== 数据绑定演示 ===")
        
        # 确保数据绑定服务已正确初始化
        if not self.data_binding_service:
            print("错误: 数据绑定服务未初始化")
            return
            
        if not self.viewmodel:
            print("错误: ViewModel未初始化")
            return
        
        # 1. 更新文章数据
        print("1. 更新文章数据...")
        self.data_binding_service.update_data('article_title', 'Updated Article Title')
        self.data_binding_service.update_data('article_content', 'This is updated content...')
        
        # 2. 添加聊天消息
        print("2. 添加聊天消息...")
        self.viewmodel.add_chat_message("System", "This is a test message from data binding")
        
        # 3. 更新文本选择
        print("3. 更新文本选择...")
        self.viewmodel.update_text_selection("selected text", 10, 20)
        
        # 4. 保存聊天历史
        print("4. 保存聊天历史...")
        chat_history = self.viewmodel.save_chat_history()
        self.data_binding_service.save_chat_history(chat_history)
        
        print("=== 演示完成 ===\n")

if __name__ == '__main__':
    # 设置窗口大小
    Window.size = (1200, 800)
    
    # 创建应用
    app = DataBindingExampleApp()
    
    # 确保应用已构建（这会调用build方法并初始化所有组件）
    app.build()
    
    # 运行演示
    app.demonstrate_data_binding()
    
    # 运行应用
    app.run() 