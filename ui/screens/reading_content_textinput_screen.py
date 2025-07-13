from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.app import App

class ReadingContentTextInputScreen(Screen):
    """文章阅读内容屏幕 - 简化TextInput版本，支持文本选择，无聊天窗口"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.article_title = ""
        self.article_content = ""
        self.article_id = None
        self.original_text = ""
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主容器
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        # 为整个页面添加白色背景
        with main_layout.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.page_bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(pos=self._update_page_bg, size=self._update_page_bg)
        
        # 1. 顶部导航栏
        self.setup_top_bar(main_layout)
        
        # 2. 文章内容区域
        self.setup_content_area(main_layout)
        
        # 3. 底部操作栏
        self.setup_bottom_bar(main_layout)
        
        self.add_widget(main_layout)
    
    def setup_top_bar(self, parent):
        """设置顶部导航栏"""
        top_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=15,
            padding=(0, 10, 0, 10)
        )
        
        # 返回按钮
        back_btn = Button(
            text='← Back',
            size_hint_x=None,
            width=100,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        back_btn.bind(on_press=self.go_back)
        
        # 标题
        self.title_label = Label(
            text='Article Title',
            size_hint_x=1,
            color=(0.2, 0.2, 0.2, 1),
            font_size=18,
            bold=True,
            halign='left',
            valign='middle'
        )
        
        top_bar.add_widget(back_btn)
        top_bar.add_widget(self.title_label)
        parent.add_widget(top_bar)
    
    def setup_content_area(self, parent):
        """设置文章内容区域"""
        # 内容滚动视图
        content_scroll = ScrollView(size_hint=(1, 1))
        
        # 内容容器
        self.content_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,  # 不自动调整高度
            height=800,  # 设置固定高度
            spacing=15,
            padding=(0, 10, 0, 10)
        )
        
        # 文章内容 - 使用TextInput实现可选择的文本
        self.content_textinput = TextInput(
            text='Loading article content...',  # 设置初始文本
            readonly=True,
            multiline=True,
            size_hint_y=1,
            background_color=(1, 1, 1, 1),  # 白色背景
            foreground_color=(0, 0, 0, 1),  # 黑色文字
            cursor_color=(0, 0, 0, 0),  # 隐藏光标
            selection_color=(0.7, 0.9, 1, 0.5),  # 蓝色选择高亮
            font_size=16,
            padding=(10, 10, 10, 10),
            scroll_x=0,
            scroll_y=1,  # 设置滚动到顶部
            input_filter=self.block_input,  # 完全阻止输入
            input_type='text',  # 文本类型
            write_tab=False  # 禁用Tab键输入
        )
        
        # 为文章内容添加白色背景
        with self.content_textinput.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.content_bg_rect = Rectangle(pos=self.content_textinput.pos, size=self.content_textinput.size)
        self.content_textinput.bind(pos=self._update_content_bg, size=self._update_content_bg)
        
        self.content_container.add_widget(self.content_textinput)
        content_scroll.add_widget(self.content_container)
        parent.add_widget(content_scroll)
        
        # 确保TextInput滚动到顶部并设置为只读
        Clock.schedule_once(self.setup_readonly, 0.1)
        
        # 定期检查文本完整性（作为备用保护）
        Clock.schedule_interval(self.check_text_integrity, 0.5)
    
    def setup_bottom_bar(self, parent):
        """设置底部操作栏"""
        bottom_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=80,
            spacing=15,
            padding=(0, 10, 0, 10)
        )
        
        # 学习按钮
        learn_btn = Button(
            text='Learn',
            size_hint_x=0.5,
            background_color=(0.2, 0.8, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        learn_btn.bind(on_press=self.start_learning)
        
        # 状态显示标签
        self.status_label = Label(
            text='Ready to read',
            size_hint_x=0.5,
            color=(0.3, 0.3, 0.3, 1),
            font_size=14
        )
        
        bottom_bar.add_widget(learn_btn)
        bottom_bar.add_widget(self.status_label)
        parent.add_widget(bottom_bar)
    
    def block_input(self, text, from_undo):
        """阻止所有输入"""
        return ''
    
    def setup_readonly(self, dt):
        """设置TextInput为完全只读模式"""
        # 设置文本内容
        if self.original_text:
            self.content_textinput.text = self.original_text
        else:
            # 如果没有原始文本，设置默认内容
            self.content_textinput.text = "No article content loaded. Please load an article first."
        
        self.content_textinput.scroll_y = 1  # 滚动到顶部
        self.content_textinput.readonly = True  # 确保只读
        self.content_textinput.focus = False  # 移除焦点
        
        # 绑定选择变化事件
        self.content_textinput.bind(selection_from=self.on_selection_change)
        self.content_textinput.bind(selection_to=self.on_selection_change)
    
    def on_selection_change(self, instance, value):
        """当文本选择发生变化时更新状态"""
        selected_text = self.get_selected_text()
        if selected_text:
            self.status_label.text = f'Selected: "{selected_text[:30]}{"..." if len(selected_text) > 30 else ""}"'
        else:
            self.status_label.text = 'Ready to read'
    
    def check_text_integrity(self, dt):
        """检查文本完整性，如果被修改则恢复"""
        if self.content_textinput.text != self.original_text:
            self.content_textinput.text = self.original_text
    
    def load_article(self, article_id, title, content):
        """加载文章内容"""
        self.article_id = article_id
        self.article_title = title
        self.article_content = content
        self.original_text = content
        
        # 更新界面
        self.title_label.text = title
        
        # 立即设置TextInput的文本
        self.content_textinput.text = content
        
        # 确保滚动到顶部
        self.content_textinput.scroll_y = 1
        
        # 添加调试信息
        print(f"Loading article: {title}")
        print(f"Article content length: {len(content)}")
        print(f"TextInput content: {self.content_textinput.text[:100]}...")
        print(f"TextInput text length: {len(self.content_textinput.text)}")
    
    def get_selected_text(self):
        """获取选中的文本"""
        try:
            # 获取选中的文本范围
            start, end = self.content_textinput.selection_from, self.content_textinput.selection_to
            if start != end:
                # 确保start是较小的索引，end是较大的索引
                if start > end:
                    start, end = end, start
                # 获取选中的文本
                selected_text = self.content_textinput.text[start:end]
                return selected_text.strip()
            else:
                return ""
        except Exception as e:
            print(f"Error getting selected text: {e}")
            return ""
    
    def go_back(self, instance):
        """返回上一页"""
        print(f"Going back to main page")
        # 返回到主屏幕
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'main'
        else:
            print("Cannot get screen manager")
    
    def start_learning(self, instance):
        """开始学习这篇文章"""
        print(f"Starting to learn article: {self.article_title}")
        # 这里可以跳转到学习页面或显示学习选项
    
    def on_enter(self):
        """屏幕进入时的回调"""
        print(f"Entering article reading page: {self.article_title}")
    
    def on_leave(self):
        """屏幕离开时的回调"""
        print("Leaving article reading page")
    
    def _update_content_bg(self, *args):
        """更新文章内容背景"""
        if hasattr(self, 'content_bg_rect'):
            self.content_bg_rect.pos = self.content_textinput.pos
            self.content_bg_rect.size = self.content_textinput.size
    
    def _update_page_bg(self, *args):
        """更新页面背景"""
        if hasattr(self, 'page_bg_rect'):
            self.page_bg_rect.pos = self.children[0].pos
            self.page_bg_rect.size = self.children[0].size


# 测试应用类
class TestReadingContentTextInputApp(App):
    """测试应用，用于单独运行reading_content_textinput_screen"""
    
    def build(self):
        # 创建屏幕管理器
        from kivy.uix.screenmanager import ScreenManager
        sm = ScreenManager()
        
        # 创建测试屏幕
        test_screen = ReadingContentTextInputScreen(name='test_reading')
        
        # 加载测试文章
        test_article = {
            'id': 1,
            'title': 'Test Article - Simplified TextInput Version',
            'content': '''This is a test article for the simplified TextInput version of the reading content screen.

You can select any part of this text using your mouse. Try selecting text from left to right, and also from right to left to test the bidirectional selection feature.

The status bar at the bottom will show you what text is currently selected.

This article contains various types of content to test:
• Short sentences
• Longer paragraphs with multiple sentences
• Special characters: !@#$%^&*()
• Numbers: 1234567890
• Mixed content: Hello World 2024!

The TextInput should be completely read-only, so you cannot edit the text, but you can select and see the selection status.

This simplified version removes the AI chat functionality to focus on basic text display and selection capabilities.'''
        }
        
        # 添加屏幕到管理器
        sm.add_widget(test_screen)
        
        # 延迟加载文章，确保UI完全初始化
        Clock.schedule_once(lambda dt: test_screen.load_article(
            test_article['id'],
            test_article['title'],
            test_article['content']
        ), 0.2)
        
        return sm


if __name__ == '__main__':
    # 设置窗口大小
    Window.size = (1000, 700)
    
    # 运行测试应用
    TestReadingContentTextInputApp().run() 