"""
Learn页面演示应用
展示语法和词汇卡片的数据绑定功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from ui.screens.learn_screen import LearnScreen
from ui.services.language_learning_binding_service import LanguageLearningBindingService
from data_managers.grammar_rule_manager import GrammarRuleManager
from data_managers.vocab_manager import VocabManager


class DemoMainScreen(Screen):
    """演示主屏幕"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "demo_main"
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # 标题
        title = Label(
            text="[b]Learn页面数据绑定演示[/b]",
            markup=True, font_size=36, size_hint_y=None, height=80
        )
        layout.add_widget(title)
        
        # 说明
        description = Label(
            text="点击下方按钮进入Learn页面，查看语法和词汇卡片的数据绑定功能",
            font_size=24, size_hint_y=None, height=100
        )
        layout.add_widget(description)
        
        # 进入Learn页面按钮
        enter_button = Button(
            text="进入Learn页面",
            font_size=28,
            size_hint_y=None,
            height=80,
            background_color=(0.2, 0.6, 1, 1)
        )
        enter_button.bind(on_press=self._on_enter_learn)
        layout.add_widget(enter_button)
        
        # 返回按钮
        back_button = Button(
            text="返回",
            font_size=24,
            size_hint_y=None,
            height=60,
            background_color=(0.8, 0.8, 0.8, 1)
        )
        back_button.bind(on_press=self._on_back)
        layout.add_widget(back_button)
        
        self.add_widget(layout)
    
    def _on_enter_learn(self, instance):
        """进入Learn页面"""
        self.manager.current = "learn_screen"
    
    def _on_back(self, instance):
        """返回"""
        App.get_running_app().stop()


class LearnScreenDemoApp(App):
    """Learn页面演示应用"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_binding_service = None
        self.grammar_manager = None
        self.vocab_manager = None
    
    def build(self):
        """构建应用"""
        # 初始化数据绑定服务
        self._initialize_data_binding_service()
        
        # 加载测试数据
        self._load_test_data()
        
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加主屏幕
        main_screen = DemoMainScreen()
        sm.add_widget(main_screen)
        
        # 添加Learn页面
        learn_screen = LearnScreen(data_binding_service=self.data_binding_service)
        # 注册ViewModel到数据绑定服务
        self.data_binding_service.register_viewmodel("LearnScreenViewModel", learn_screen.viewmodel)
        sm.add_widget(learn_screen)
        
        return sm
    
    def _initialize_data_binding_service(self):
        """初始化数据绑定服务"""
        self.data_binding_service = LanguageLearningBindingService()
        
        # 初始化语法和词汇管理器
        self.grammar_manager = GrammarRuleManager()
        self.vocab_manager = VocabManager()
        
        # 加载数据文件
        try:
            self.grammar_manager.load_from_file("data/grammar_rules.json")
            print("✅ 语法规则数据加载成功")
        except Exception as e:
            print(f"❌ 语法规则数据加载失败: {e}")
        
        try:
            self.vocab_manager.load_from_file("data/vocab_expressions.json")
            print("✅ 词汇表达数据加载成功")
        except Exception as e:
            print(f"❌ 词汇表达数据加载失败: {e}")
        
        # 将数据注册到绑定服务
        self._register_data_to_binding_service()
    
    def _register_data_to_binding_service(self):
        """将数据注册到绑定服务"""
        # 注册语法数据
        grammar_bundles = self.grammar_manager.grammar_bundles
        self.data_binding_service.update_data("grammar_bundles", grammar_bundles)
        self.data_binding_service.update_data("grammar_loading", False)
        self.data_binding_service.update_data("grammar_error", "")
        self.data_binding_service.update_data("total_grammar_rules", len(grammar_bundles))
        
        # 注册词汇数据
        vocab_bundles = self.vocab_manager.vocab_bundles
        self.data_binding_service.update_data("vocab_bundles", vocab_bundles)
        self.data_binding_service.update_data("vocab_loading", False)
        self.data_binding_service.update_data("vocab_error", "")
        self.data_binding_service.update_data("total_vocab_expressions", len(vocab_bundles))
        
        print(f"✅ 数据注册成功: {len(grammar_bundles)} 个语法规则, {len(vocab_bundles)} 个词汇表达")
    
    def _load_test_data(self):
        """加载测试数据（如果数据文件为空）"""
        if not self.grammar_manager.grammar_bundles:
            print("📝 添加测试语法规则...")
            self._add_test_grammar_rules()
        
        if not self.vocab_manager.vocab_bundles:
            print("📝 添加测试词汇表达...")
            self._add_test_vocab_expressions()
    
    def _add_test_grammar_rules(self):
        """添加测试语法规则"""
        # 添加一些测试语法规则
        rule1_id = self.grammar_manager.add_new_rule(
            "主谓一致",
            "英语中主语和谓语动词必须在人称和数上保持一致"
        )
        
        rule2_id = self.grammar_manager.add_new_rule(
            "时态用法",
            "英语中不同时态用于表达不同的时间概念和动作状态"
        )
        
        rule3_id = self.grammar_manager.add_new_rule(
            "从句结构",
            "英语从句是复合句的重要组成部分，包括名词从句、形容词从句和副词从句"
        )
        
        print(f"✅ 添加了 {len(self.grammar_manager.grammar_bundles)} 个测试语法规则")
    
    def _add_test_vocab_expressions(self):
        """添加测试词汇表达"""
        # 添加一些测试词汇表达
        vocab1_id = self.vocab_manager.add_new_vocab(
            "in which",
            "用于引导定语从句，表示'在其中'的意思"
        )
        
        vocab2_id = self.vocab_manager.add_new_vocab(
            "currently",
            "副词，表示'目前'、'当前'的意思"
        )
        
        vocab3_id = self.vocab_manager.add_new_vocab(
            "sowie",
            "德语连接词，表示'以及'、'还有'的意思"
        )
        
        vocab4_id = self.vocab_manager.add_new_vocab(
            "encyclopedia",
            "百科全书，包含各种知识的参考书籍"
        )
        
        vocab5_id = self.vocab_manager.add_new_vocab(
            "free content",
            "自由内容，可以自由使用、修改和分发的内容"
        )
        
        print(f"✅ 添加了 {len(self.vocab_manager.vocab_bundles)} 个测试词汇表达")
    
    def on_stop(self):
        """应用停止时清理资源"""
        if self.data_binding_service:
            # 清理数据绑定服务
            for viewmodel_name in list(self.data_binding_service._viewmodels.keys()):
                self.data_binding_service.unregister_viewmodel(viewmodel_name)
        print("👋 Learn页面演示应用已停止")


if __name__ == "__main__":
    print("🚀 启动Learn页面数据绑定演示...")
    print("=" * 50)
    
    try:
        app = LearnScreenDemoApp()
        app.run()
    except Exception as e:
        print(f"❌ 应用运行失败: {e}")
        import traceback
        traceback.print_exc() 