from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock

class TextInputTestModuleApp(App):
    def build(self):
        # 主布局
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title = Label(text='TextInput Test Module', size_hint_y=None, height=50)
        layout.add_widget(title)
        
        # 文章内容区域
        content_layout = BoxLayout(orientation='vertical', size_hint_y=0.8)
        
        # 文章标题
        article_title = Label(
            text='Test Article Title',
            size_hint_y=None,
            height=40,
            bold=True
        )
        content_layout.add_widget(article_title)
        
        # 保存原始文本
        self.original_text = 'This is a test article content.\n\nYou can select any part of this text.\n\nThis is more test content to verify that the text selection function works properly.\n\nYou can use the get_selected_text() method to retrieve selected text programmatically.'
        
        # 文章内容 - 使用TextInput实现可选择的文本
        self.article_content = TextInput(
            text='',  # 先设置为空
            readonly=True,
            multiline=True,
            size_hint_y=1,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 0),  # 隐藏光标
            selection_color=(0.7, 0.9, 1, 0.5),
            font_size=16,
            padding=(10, 10),
            scroll_x=0,
            scroll_y=1,  # 设置滚动到顶部
            input_filter=self.block_input,  # 完全阻止输入
            input_type='text',  # 文本类型
            write_tab=False  # 禁用Tab键输入
        )
        

        content_layout.add_widget(self.article_content)
        
        layout.add_widget(content_layout)
        
        # 状态显示区域
        self.status_label = Label(
            text='Status: Ready - Select text to test get_selected_text()',
            size_hint_y=None,
            height=40,
            color=(0.5, 0.5, 0.5, 1)
        )
        layout.add_widget(self.status_label)
        
        # 选中文本显示区域
        self.selection_label = Label(
            text='Selection: None',
            size_hint_y=None,
            height=80,
            color=(0.3, 0.7, 0.3, 1),
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        layout.add_widget(self.selection_label)
        
        # 确保TextInput滚动到顶部并设置为只读
        Clock.schedule_once(self.setup_readonly, 0.1)
        
        # 定期检查文本完整性（作为备用保护）
        Clock.schedule_interval(self.check_text_integrity, 0.5)
        
        # 定期更新选中文本显示
        Clock.schedule_interval(self.update_selection_display, 0.1)
        
        return layout
    
    def block_input(self, text, from_undo):
        """阻止所有输入"""
        return ''
    
    def setup_readonly(self, dt):
        """设置TextInput为完全只读模式"""
        # 设置文本内容
        self.article_content.text = self.original_text
        self.article_content.scroll_y = 1  # 滚动到顶部
        self.article_content.readonly = True  # 确保只读
        self.article_content.focus = False  # 移除焦点
    
    def check_text_integrity(self, dt):
        """检查文本完整性，如果被修改则恢复"""
        if self.article_content.text != self.original_text:
            self.article_content.text = self.original_text
    
    def update_selection_display(self, dt):
        """更新选中文本显示"""
        try:
            # 获取选择范围
            start, end = self.article_content.selection_from, self.article_content.selection_to
            selected_text = self.get_selected_text()
            
            if selected_text:
                # 显示选中的文本（限制长度避免显示过长）
                display_text = selected_text[:50] + "..." if len(selected_text) > 50 else selected_text
                self.selection_label.text = f'Selection: "{display_text}" (Range: {start}-{end})'
                self.status_label.text = f'Status: Text selected ({len(selected_text)} chars)'
            else:
                self.selection_label.text = f'Selection: None (Range: {start}-{end})'
                self.status_label.text = 'Status: No text selected'
        except Exception as e:
            self.selection_label.text = f'Selection: Error - {e}'
            self.status_label.text = 'Status: Error getting selection'
    

    
    def get_selected_text(self):
        """获取选中的文本"""
        try:
            # 获取选中的文本范围
            start, end = self.article_content.selection_from, self.article_content.selection_to
            if start != end:
                # 确保start是较小的索引，end是较大的索引
                if start > end:
                    start, end = end, start
                # 获取选中的文本
                selected_text = self.article_content.text[start:end]
                return selected_text.strip()
            else:
                return ""
        except Exception as e:
            print(f"Error getting selected text: {e}")
            return ""
    
    def update_status(self, text):
        """更新状态显示"""
        self.status_label.text = f'Status: {text}'
        # 同时更新选中文本显示
        self.update_selection_display(None)

if __name__ == '__main__':
    # 设置窗口大小
    Window.size = (800, 600)
    app = TextInputTestModuleApp()
    
    # 示例：如何获取选中的文本
    def test_selection():
        selected = app.get_selected_text()
        if selected:
            print(f"Selected text: '{selected}'")
            app.update_status(f"Selected: '{selected[:30]}...'")
        else:
            print("No text selected")
            app.update_status("No text selected")
    
    # 添加键盘快捷键来测试选择功能
    def on_keyboard(window, key, scancode, codepoint, modifier):
        if key == 13:  # Enter键
            test_selection()
            return True
        return False
    
    # 绑定键盘事件
    from kivy.core.window import Window
    Window.bind(on_keyboard=on_keyboard)
    
    # 可以在这里调用 test_selection() 来测试文本选择功能
    # test_selection()
    
    app.run() 