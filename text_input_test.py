from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window

class TextInputTestApp(App):
    def build(self):
        # 主布局
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title = Label(text='TextInput Test', size_hint_y=None, height=50)
        layout.add_widget(title)
        
        # 文章内容区域
        content_layout = BoxLayout(orientation='vertical', size_hint_y=0.6)
        
        # 文章标题
        article_title = Label(
            text='Test Article Title',
            size_hint_y=None,
            height=40,
            bold=True
        )
        content_layout.add_widget(article_title)
        
        # 文章内容 - 使用TextInput实现可选择的文本
        self.article_content = TextInput(
            text='This is a test article content.\n\nYou can select any part of this text.\n\nAfter selecting text, click the buttons below to quote or send the selected content.\n\nThis is more test content to verify that the text selection function works properly.',
            readonly=True,
            multiline=True,
            size_hint_y=1,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 1),
            selection_color=(0.7, 0.9, 1, 0.5),
            font_size=16,
            padding=(10, 10),
            scroll_x=0,
            scroll_y=1  # 设置滚动到顶部
        )
        content_layout.add_widget(self.article_content)
        
        layout.add_widget(content_layout)
        
        # 按钮区域
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        # 引用选中按钮
        self.quote_btn = Button(
            text='Quote Selected',
            size_hint_x=0.5,
            background_color=(0.2, 0.6, 1, 1)
        )
        self.quote_btn.bind(on_press=self.quote_selected)
        button_layout.add_widget(self.quote_btn)
        
        # 发送选中按钮
        self.send_btn = Button(
            text='Send Selected',
            size_hint_x=0.5,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.send_btn.bind(on_press=self.send_selected)
        button_layout.add_widget(self.send_btn)
        
        layout.add_widget(button_layout)
        
        # 状态显示区域
        self.status_label = Label(
            text='Status: Waiting for text selection...',
            size_hint_y=None,
            height=40,
            color=(0.5, 0.5, 0.5, 1)
        )
        layout.add_widget(self.status_label)
        
        # 聊天输入区域
        chat_layout = BoxLayout(orientation='vertical', size_hint_y=0.3)
        
        chat_label = Label(text='Chat Input:', size_hint_y=None, height=30)
        chat_layout.add_widget(chat_label)
        
        self.chat_input = TextInput(
            text='',
            multiline=True,
            size_hint_y=1,
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0, 0, 0, 1),
            font_size=14,
            padding=(10, 10)
        )
        chat_layout.add_widget(self.chat_input)
        
        layout.add_widget(chat_layout)
        
        # 确保TextInput滚动到顶部
        from kivy.clock import Clock
        Clock.schedule_once(self.scroll_to_top, 0.1)
        
        return layout
    
    def scroll_to_top(self, dt):
        """确保TextInput滚动到顶部"""
        self.article_content.scroll_y = 1
    
    def quote_selected(self, instance):
        """引用选中的文本"""
        selected_text = self.get_selected_text()
        if selected_text:
            # 在聊天输入框中添加引用的文本
            current_text = self.chat_input.text
            quoted_text = f'Quote: "{selected_text}"\n'
            self.chat_input.text = quoted_text + current_text
            self.status_label.text = f'Status: Quoted "{selected_text[:20]}..."'
        else:
            self.status_label.text = 'Status: No text selected'
    
    def send_selected(self, instance):
        """发送选中的文本"""
        selected_text = self.get_selected_text()
        if selected_text:
            # 直接发送到聊天输入框
            current_text = self.chat_input.text
            new_text = f'Send: {selected_text}\n'
            self.chat_input.text = current_text + new_text
            self.status_label.text = f'Status: Sent "{selected_text[:20]}..."'
        else:
            self.status_label.text = 'Status: No text selected'
    
    def get_selected_text(self):
        """获取选中的文本"""
        try:
            # 获取选中的文本范围
            start, end = self.article_content.selection_from, self.article_content.selection_to
            if start != end:
                # 获取选中的文本
                selected_text = self.article_content.text[start:end]
                return selected_text.strip()
            else:
                return ""
        except Exception as e:
            print(f"Error getting selected text: {e}")
            return ""

if __name__ == '__main__':
    # 设置窗口大小
    Window.size = (800, 600)
    TextInputTestApp().run() 