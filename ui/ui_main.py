# ui_main.py
from kivy.app import App  # Kivy 应用主类
from kivy.uix.boxlayout import BoxLayout  # 用于垂直布局
from kivy.uix.textinput import TextInput  # 文本输入框
from kivy.uix.button import Button  # 按钮
from kivy.uix.label import Label  # 标签，显示文本
from kivy.uix.scrollview import ScrollView  # 新增导入
from kivy.utils import get_color_from_hex  # 用于颜色
from main_assistant import MainAssistant  # 引入你写好的后端助手类
from kivy.graphics import Color, Line

# 主UI组件，继承BoxLayout，表示一个竖排布局的界面
class AICHAT(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)  # 设为竖直方向的布局
        self.background_color = get_color_from_hex('#FFFFFF')  # 设置主背景为白色
        self.canvas.before.clear()  # type: ignore
        with self.canvas.before:  # type: ignore
            from kivy.graphics import Color, Rectangle
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)  # type: ignore
        self.bind(pos=self._update_bg, size=self._update_bg)  # type: ignore

        # 上半部分留空
        self.top_blank = BoxLayout(size_hint_y=0.5)
        self.add_widget(self.top_blank)

        # 聊天窗口外层加黑色边框
        chat_border_box = BoxLayout(orientation='vertical', size_hint_y=0.5, padding=1)
        with chat_border_box.canvas.before:  # type: ignore
            Color(0, 0, 0, 1)
            chat_border_box.border_line = Line(rectangle=(chat_border_box.x, chat_border_box.y, chat_border_box.width, chat_border_box.height), width=1)  # type: ignore
        def update_border_line(instance, value):
            chat_border_box.border_line.rectangle = (chat_border_box.x, chat_border_box.y, chat_border_box.width, chat_border_box.height)  # type: ignore
        chat_border_box.bind(pos=update_border_line, size=update_border_line)  # type: ignore
        bottom_box = BoxLayout(orientation='vertical')

        # 标题
        title_label = Label(text='ask ai', size_hint_y=None, height=32, color=get_color_from_hex('#000000'), font_size=35, bold=True)
        bottom_box.add_widget(title_label)

        # 初始化你的 AI 助手类
        self.assistant = MainAssistant()

        # 聊天记录区（可滚动）
        self.chat_history_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.chat_history_layout.bind(minimum_height=self.chat_history_layout.setter('height'))  # type: ignore
        self.scroll = ScrollView(size_hint=(1, 1))
        self.scroll.add_widget(self.chat_history_layout)
        bottom_box.add_widget(self.scroll)

        # 输入区（横向排列，固定底部）
        self.input = TextInput(hint_text="Please enter your question", size_hint_x=0.8, multiline=False)
        self.button = Button(text="Send", size_hint_x=0.2)
        self.button.bind(on_press=self.on_send)  # type: ignore
        input_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        input_box.add_widget(self.input)
        input_box.add_widget(self.button)
        bottom_box.add_widget(input_box)

        chat_border_box.add_widget(bottom_box)
        self.add_widget(chat_border_box)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def add_message(self, text, is_user):
        # 区分用户和AI颜色
        if is_user:
            color = get_color_from_hex('#333333')  # 深灰
            halign = 'right'
            bg_color = get_color_from_hex('#EEEEEE')  # 浅灰底
        else:
            color = get_color_from_hex('#000000')  # 黑色
            halign = 'left'
            bg_color = get_color_from_hex('#FFFFFF')  # 白底
        msg_box = BoxLayout(size_hint_y=None, height=34, padding=[5,2,5,2])
        with msg_box.canvas.before:  # type: ignore
            from kivy.graphics import Color, Rectangle
            Color(*bg_color)
            msg_box.bg_rect = Rectangle(pos=msg_box.pos, size=msg_box.size)  # type: ignore
        def update_bg_rect(instance, value):
            msg_box.bg_rect.pos = msg_box.pos  # type: ignore
            msg_box.bg_rect.size = msg_box.size  # type: ignore
        msg_box.bind(pos=update_bg_rect, size=update_bg_rect)  # type: ignore
        label = Label(text=text, size_hint_y=None, height=30, color=color, halign=halign, valign='middle')
        label.bind(texture_size=label.setter('size'))  # type: ignore
        msg_box.add_widget(label)
        self.chat_history_layout.add_widget(msg_box)

    # 事件处理函数：当按钮被点击时触发
    def on_send(self, instance):
        user_text = self.input.text.strip()
        if not user_text:
            return
        self.add_message(user_text, is_user=True)
        reply = self.assistant.answer(user_text)
        self.add_message(reply, is_user=False)
        self.input.text = ''


class MainUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        # 阅读材料区
        self.article_expanded = True
        self.article_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.article_box.height = 220
        self.article_title = Label(text='Text Title', font_size=30, bold=True, size_hint_y=None, height=40)
        self.article_content_scroll = ScrollView(size_hint_y=None, height=120)
        self.article_content = Label(text='这里是阅读材料内容...\n可以很多很多行\n支持滚动', size_hint_y=None)
        self.article_content.bind(texture_size=self.article_content.setter('size'))  # type: ignore
        self.article_content_scroll.add_widget(self.article_content)
        self.toggle_btn = Button(text='收起', size_hint_y=None, height=30)
        self.toggle_btn.bind(on_press=self.toggle_article)  # type: ignore
        self.article_box.add_widget(self.article_title)
        self.article_box.add_widget(self.article_content_scroll)
        self.article_box.add_widget(self.toggle_btn)
        self.add_widget(self.article_box)

        # AI Chat 区（可展开/收起）
        self.ai_expanded = True
        self.ai_chat_box = BoxLayout(orientation='vertical')
        self.ai_title_btn = Button(text='ask ai', size_hint_y=None, height=40, font_size=25, bold=True)
        self.ai_title_btn.bind(on_press=self.toggle_ai_chat)  # type: ignore
        self.ai_chat_box.add_widget(self.ai_title_btn)
        self.ai_chat = AICHAT()
        self.ai_chat_box.add_widget(self.ai_chat)
        self.add_widget(self.ai_chat_box)

    def toggle_article(self, instance):
        if self.article_expanded:
            self.article_content_scroll.height = 0
            self.toggle_btn.text = '展开'
            self.article_box.height = 70
            self.article_expanded = False
        else:
            self.article_content_scroll.height = 120
            self.toggle_btn.text = '收起'
            self.article_box.height = 220
            self.article_expanded = True

    def toggle_ai_chat(self, instance):
        if self.ai_expanded:
            self.ai_chat.height = 0
            self.ai_chat.size_hint_y = None
            self.ai_expanded = False
        else:
            self.ai_chat.height = 1
            self.ai_chat.size_hint_y = 1
            self.ai_expanded = True


# Kivy 应用的入口类
class LanguageApp(App):
    def build(self):
        return MainUI()


# 程序主入口
if __name__ == '__main__':
    LanguageApp().run()
