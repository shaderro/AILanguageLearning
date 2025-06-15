from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window

# 模拟数据
EXPLANATIONS = {
    "Ich bin ein Student.": "语法：'sein' 动词变位；词汇：Student（学生）是阳性名词。",
    "Heute ist das Wetter schön.": "语法：主语+动词+表语；词汇：Wetter（天气）、schön（好）。",
    "Wir lernen Deutsch.": "语法：'lernen' 为规则动词；词汇：Deutsch 表示德语。",
}

SENTENCES = list(EXPLANATIONS.keys())


class LanguageLearningApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)  # 白底

        # 整体垂直布局
        root = BoxLayout(orientation='vertical')

        # 顶部：句子列表 ScrollView
        self.sentence_list = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=10)
        self.sentence_list.bind(minimum_height=self.sentence_list.setter('height'))

        for sentence in SENTENCES:
            btn = Button(
                text=sentence,
                size_hint_y=None,
                height=40,
                background_normal='',
                background_color=(1, 1, 1, 1),
                color=(0, 0, 0, 1),
                halign='left'
            )
            btn.bind(on_press=self.show_explanation)
            self.sentence_list.add_widget(btn)

        scroll_sentences = ScrollView(size_hint=(1, 0.5))
        scroll_sentences.add_widget(self.sentence_list)

        root.add_widget(scroll_sentences)

        # 底部：讲解 ScrollView
        self.explanation_label = Label(
            text="please select a sentence",
            size_hint_y=None,
            text_size=(Window.width - 40, None),  # 自动换行
            color=(0, 0, 0, 1),
            halign='left',
            valign='top',
            padding=(10, 10)
        )
        self.explanation_label.bind(texture_size=self.update_label_height)

        explanation_layout = BoxLayout(orientation='vertical', padding=10)
        explanation_layout.add_widget(self.explanation_label)

        scroll_explanation = ScrollView(size_hint=(1, 0.5))
        scroll_explanation.add_widget(explanation_layout)

        root.add_widget(scroll_explanation)

        return root

    def update_label_height(self, instance, value):
        instance.height = instance.texture_size[1] + 20

    def show_explanation(self, instance):
        sentence = instance.text
        explanation = EXPLANATIONS.get(sentence, "无讲解。")
        self.explanation_label.text = explanation

        # 高亮当前点击句子
        for btn in self.sentence_list.children:
            btn.background_color = (1, 1, 1, 1)
        instance.background_color = (0.8, 0.8, 1, 1)


if __name__ == '__main__':
    LanguageLearningApp().run()
