from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

class ReadContentScreen(Screen):
    """简易文章内容屏幕"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.article_title = ""
        self.article_content = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        # 顶部返回按钮和标题
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        back_btn = Button(text='返回', size_hint_x=None, width=80)
        back_btn.bind(on_press=self.go_back)
        self.title_label = Label(text='标题', size_hint_x=1, halign='left', valign='middle')
        top_bar.add_widget(back_btn)
        top_bar.add_widget(self.title_label)
        layout.add_widget(top_bar)
        # 内容滚动区
        scroll = ScrollView(size_hint_y=1)
        self.content_label = Label(text='内容', size_hint_y=None, halign='left', valign='top')
        self.content_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll.add_widget(self.content_label)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def load_article(self, title, content):
        self.article_title = title
        self.article_content = content
        self.title_label.text = title
        self.content_label.text = content

    def go_back(self, instance):
        if self.manager:
            self.manager.current = 'main' 