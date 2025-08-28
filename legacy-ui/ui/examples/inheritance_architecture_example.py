"""
基于继承架构的示例应用
展示如何使用BaseViewModel和BaseDataBindingService
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

# 导入我们的架构组件
from services.language_learning_binding_service import LanguageLearningBindingService
from viewmodels.text_input_chat_viewmodel import TextInputChatViewModel

class InheritanceArchitectureExampleApp(App):
    """基于继承架构的示例应用"""
    
    def build(self):
        # 创建屏幕管理器
        self.sm = ScreenManager()
        
        # 创建数据绑定服务
        self.binding_service = LanguageLearningBindingService()
        
        # 添加主屏幕
        main_screen = MainScreen(self.binding_service, name="main")
        self.sm.add_widget(main_screen)
        
        # 添加聊天屏幕
        chat_screen = ChatScreen(self.binding_service, name="chat")
        self.sm.add_widget(chat_screen)
        
        return self.sm

class MainScreen(Screen):
    """主屏幕"""
    
    def __init__(self, binding_service, **kwargs):
        super().__init__(**kwargs)
        self.binding_service = binding_service
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 标题
        title = Label(
            text='基于继承的MVVM架构示例',
            size_hint_y=None,
            height=50,
            font_size=20,
            bold=True
        )
        layout.add_widget(title)
        
        # 说明
        description = Label(
            text='这个示例展示了如何使用BaseViewModel和BaseDataBindingService\n'
                 '实现可扩展的MVVM架构',
            size_hint_y=None,
            height=80,
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        layout.add_widget(description)
        
        # 功能按钮
        buttons_layout = BoxLayout(orientation='vertical', spacing=10)
        
        # 测试数据绑定按钮
        test_binding_btn = Button(
            text='测试数据绑定',
            size_hint_y=None,
            height=50,
            on_press=self.test_data_binding
        )
        buttons_layout.add_widget(test_binding_btn)
        
        # 测试ViewModel生命周期按钮
        test_lifecycle_btn = Button(
            text='测试ViewModel生命周期',
            size_hint_y=None,
            height=50,
            on_press=self.test_viewmodel_lifecycle
        )
        buttons_layout.add_widget(test_lifecycle_btn)
        
        # 跳转到聊天页面按钮
        go_chat_btn = Button(
            text='跳转到聊天页面',
            size_hint_y=None,
            height=50,
            on_press=self.go_to_chat
        )
        buttons_layout.add_widget(go_chat_btn)
        
        layout.add_widget(buttons_layout)
        
        # 状态显示
        self.status_label = Label(
            text='状态: 就绪',
            size_hint_y=None,
            height=40,
            color=(0.5, 0.5, 0.5, 1)
        )
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
    
    def test_data_binding(self, instance):
        """测试数据绑定功能"""
        try:
            # 创建测试ViewModel
            test_viewmodel = TestViewModel(self.binding_service)
            
            # 注册ViewModel
            self.binding_service.register_viewmodel("test", test_viewmodel)
            
            # 创建数据绑定
            self.binding_service.bind_data_to_viewmodel("test_data", "test", "test_property")
            
            # 更新数据
            self.binding_service.update_data("test_data", "Hello from Data Binding Service!")
            
            # 检查ViewModel是否收到数据
            if test_viewmodel.test_property == "Hello from Data Binding Service!":
                self.status_label.text = "状态: 数据绑定测试成功"
                self.status_label.color = (0, 1, 0, 1)
            else:
                self.status_label.text = "状态: 数据绑定测试失败"
                self.status_label.color = (1, 0, 0, 1)
            
            # 清理
            test_viewmodel.destroy()
            
        except Exception as e:
            self.status_label.text = f"状态: 数据绑定测试失败 - {e}"
            self.status_label.color = (1, 0, 0, 1)
    
    def test_viewmodel_lifecycle(self, instance):
        """测试ViewModel生命周期"""
        try:
            # 创建测试ViewModel
            test_viewmodel = TestViewModel(self.binding_service)
            
            # 检查初始化状态
            if test_viewmodel._initialized:
                self.status_label.text = "状态: ViewModel生命周期测试成功"
                self.status_label.color = (0, 1, 0, 1)
            else:
                self.status_label.text = "状态: ViewModel初始化失败"
                self.status_label.color = (1, 0, 0, 1)
            
            # 测试销毁
            test_viewmodel.destroy()
            
        except Exception as e:
            self.status_label.text = f"状态: ViewModel生命周期测试失败 - {e}"
            self.status_label.color = (1, 0, 0, 1)
    
    def go_to_chat(self, instance):
        """跳转到聊天页面"""
        self.manager.current = "chat"

class ChatScreen(Screen):
    """聊天屏幕"""
    
    def __init__(self, binding_service, **kwargs):
        super().__init__(**kwargs)
        self.binding_service = binding_service
        self.viewmodel = None
        self._setup_ui()
        self._setup_viewmodel()
    
    def _setup_ui(self):
        """设置UI"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title = Label(
            text='聊天页面 - 继承架构示例',
            size_hint_y=None,
            height=40,
            font_size=18,
            bold=True
        )
        layout.add_widget(title)
        
        # 文章内容区域
        content_layout = BoxLayout(orientation='vertical', size_hint_y=0.6)
        
        # 文章标题
        self.article_title_label = Label(
            text='文章标题',
            size_hint_y=None,
            height=30,
            bold=True
        )
        content_layout.add_widget(self.article_title_label)
        
        # 文章内容
        self.article_content = TextInput(
            text='',
            readonly=True,
            multiline=True,
            size_hint_y=1,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 0),
            selection_color=(0.7, 0.9, 1, 0.5),
            font_size=14,
            padding=(10, 10)
        )
        content_layout.add_widget(self.article_content)
        
        layout.add_widget(content_layout)
        
        # 聊天消息区域
        chat_layout = BoxLayout(orientation='vertical', size_hint_y=0.3)
        
        # 聊天消息标题
        chat_title = Label(
            text='聊天消息',
            size_hint_y=None,
            height=25,
            bold=True
        )
        chat_layout.add_widget(chat_title)
        
        # 聊天消息滚动区域
        self.chat_scroll = ScrollView(size_hint_y=1)
        self.chat_grid = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=5,
            padding=5
        )
        self.chat_grid.bind(minimum_height=lambda instance, value: setattr(self.chat_grid, 'height', value))
        self.chat_scroll.add_widget(self.chat_grid)
        chat_layout.add_widget(self.chat_scroll)
        
        layout.add_widget(chat_layout)
        
        # 输入区域
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        self.input_field = TextInput(
            text='',
            multiline=False,
            size_hint_x=0.8,
            hint_text='输入消息...'
        )
        input_layout.add_widget(self.input_field)
        
        send_btn = Button(
            text='发送',
            size_hint_x=0.2,
            on_press=self.send_message
        )
        input_layout.add_widget(send_btn)
        
        layout.add_widget(input_layout)
        
        # 返回按钮
        back_btn = Button(
            text='返回主页面',
            size_hint_y=None,
            height=40,
            on_press=self.go_back
        )
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def _setup_viewmodel(self):
        """设置ViewModel"""
        # 创建ViewModel
        self.viewmodel = TextInputChatViewModel(self.binding_service)
        
        # 绑定UI到ViewModel
        self.article_title_label.bind(text=self.viewmodel.setter('article_title'))
        self.article_content.bind(text=self.viewmodel.setter('article_content'))
        self.input_field.bind(text=self.viewmodel.setter('current_input'))
        
        # 绑定ViewModel到UI
        self.viewmodel.bind(chat_messages=self.update_chat_display)
    
    def update_chat_display(self, instance, value):
        """更新聊天显示"""
        self.chat_grid.clear_widgets()
        for message in value:
            msg_label = Label(
                text=f"{message['sender']}: {message['message']}",
                size_hint_y=None,
                height=40,
                text_size=(None, None),
                halign='left',
                valign='top',
                color=(0, 0, 0, 1) if message['is_ai'] else (0.2, 0.2, 0.8, 1)
            )
            self.chat_grid.add_widget(msg_label)
    
    def send_message(self, instance):
        """发送消息"""
        if self.viewmodel:
            message = self.viewmodel.current_input
            if message.strip():
                self.viewmodel.send_message(message)
    
    def go_back(self, instance):
        """返回主页面"""
        if self.viewmodel:
            self.viewmodel.destroy()
        self.manager.current = "main"

class TestViewModel(TextInputChatViewModel):
    """测试用的ViewModel"""
    
    def __init__(self, data_binding_service=None, **kwargs):
        super().__init__(data_binding_service=data_binding_service, **kwargs)
        self.test_property = "initial_value"
    
    def on_initialize(self):
        """测试初始化"""
        super().on_initialize()
        self.test_property = "initialized"
        print("TestViewModel: 初始化完成")

if __name__ == '__main__':
    InheritanceArchitectureExampleApp().run() 