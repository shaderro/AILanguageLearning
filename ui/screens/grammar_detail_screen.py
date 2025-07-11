from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle

class GrammarDetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_ui()

    def setup_ui(self):
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=0, spacing=0)
        # 内容区外层加padding和圆角白底
        content_outer = BoxLayout(orientation='vertical', padding=10, size_hint_y=0.92)
        with content_outer.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(pos=content_outer.pos, size=content_outer.size, radius=[20])
        content_outer.bind(pos=self._update_bg, size=self._update_bg)

        # 顶部返回按钮
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, padding=(5, 0, 0, 0))
        back_btn = Button(text='<', size_hint_x=None, width=40, background_color=(0,0,0,0), color=(0,0,0,1), font_size=20)
        back_btn.bind(on_press=self.go_back)
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Widget())
        content_outer.add_widget(top_bar)

        # 滚动内容区
        scroll = ScrollView(size_hint_y=1)
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=(10,0,10,0))
        content_box.bind(minimum_height=lambda inst, val: setattr(content_box, 'height', val))

        # 语法标题
        grammar_label = Label(text='[b]Grammar1[/b]', markup=True, font_size=20, color=(0,0,0,1), size_hint_y=None, height=30, halign='left', valign='middle')
        grammar_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(grammar_label)
        # 简要解释
        brief_label = Label(text='a brief explanation ...', font_size=16, color=(0,0,0,1), size_hint_y=None, height=25, halign='left', valign='top')
        brief_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(brief_label)
        # Example区块
        example_title = Label(text='[b]Example[/b]', markup=True, font_size=16, color=(0,0,0,1), size_hint_y=None, height=25, halign='left', valign='middle')
        example_title.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(example_title)
        example_sentence = Label(text='An example sentence', font_size=15, color=(0,0,0,1), size_hint_y=None, height=22, halign='left', valign='top')
        example_sentence.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(example_sentence)
        # 相关语法
        relevant_label = Label(text='Relevant vocab', font_size=15, color=(0,0,0,1), size_hint_y=None, height=22, halign='left', valign='middle')
        relevant_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(relevant_label)
        grammar2_label = Label(text='[b]Grammar2[/b]', markup=True, font_size=16, color=(0,0,0,1), size_hint_y=None, height=25, halign='left', valign='middle')
        grammar2_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, None)))
        content_box.add_widget(grammar2_label)
        scroll.add_widget(content_box)
        content_outer.add_widget(scroll)
        main_layout.add_widget(content_outer)

        # 底部tab栏
        tab_bar = BoxLayout(orientation='horizontal', size_hint_y=0.08, height=40)
        read_btn = Button(text='read', background_color=(1,1,1,1), color=(0,0,0,1), font_size=16)
        review_btn = Button(text='review', background_color=(1,1,1,1), color=(0,0,0,1), font_size=16)
        tab_bar.add_widget(read_btn)
        tab_bar.add_widget(review_btn)
        main_layout.add_widget(tab_bar)

        self.add_widget(main_layout)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.children[0].pos
        self.bg_rect.size = self.children[0].size

    def go_back(self, instance):
        # 返回上一页逻辑
        if self.manager:
            self.manager.current = 'main'