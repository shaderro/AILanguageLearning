"""
Token选择功能测试脚本
测试基于词/短语的选择机制
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.clock import Clock
from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest

class TokenSelectionTestApp(App):
    """Token选择功能测试应用"""
    
    def build(self):
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加测试聊天屏幕
        self.test_chat_screen = TextInputChatScreenTest(name='test_chat')
        sm.add_widget(self.test_chat_screen)
        
        # 运行测试功能
        self.test_chat_screen.test_run()
        
        # 延迟执行自动测试
        Clock.schedule_once(self.run_automated_test, 2.0)
        
        print("\n🎯 Token选择功能测试说明:")
        print("1. 文章内容现在基于词/短语显示")
        print("2. 每个词/短语都是独立的可点击区域")
        print("3. 可以通过点击和拖拽选择词/短语")
        print("4. 选择范围限制在词/短语级别")
        print("5. 观察控制台输出，查看选择状态")
        
        return sm
    
    def run_automated_test(self, dt):
        """运行自动测试"""
        print("\n🧪 开始自动测试Token选择功能...")
        
        # 检查分词结果
        if hasattr(self.test_chat_screen, 'tokens'):
            print(f"📝 分词结果: {self.test_chat_screen.tokens}")
            print(f"📝 Token数量: {len(self.test_chat_screen.tokens)}")
            
            # 模拟选择第一个token
            if len(self.test_chat_screen.token_widgets) > 0:
                first_token = self.test_chat_screen.token_widgets[0]
                print(f"🎯 模拟选择第一个token: '{first_token.token_text}'")
                
                # 直接调用选择逻辑，避免使用MotionEvent
                self.test_chat_screen.selection_start_index = first_token.token_index
                self.test_chat_screen.selection_end_index = first_token.token_index
                self.test_chat_screen._highlight_token(first_token, True)
                self.test_chat_screen._update_selection_from_tokens()
                
                # 检查选择状态
                Clock.schedule_once(self.check_token_selection, 0.5)
        else:
            print("❌ 没有找到tokens，测试失败")
    
    def check_token_selection(self, dt):
        """检查token选择状态"""
        print("\n📊 检查Token选择状态:")
        print(f"✅ 选择开始索引: {self.test_chat_screen.selection_start_index}")
        print(f"✅ 选择结束索引: {self.test_chat_screen.selection_end_index}")
        print(f"✅ 选中文本: '{self.test_chat_screen.selected_text_backup}'")
        print(f"✅ 选择状态: {self.test_chat_screen.is_text_selected}")
        
        # 检查是否有选中的token
        selected_tokens = []
        for i, token_widget in enumerate(self.test_chat_screen.token_widgets):
            if token_widget.is_selected:
                selected_tokens.append(token_widget.token_text)
        
        print(f"✅ 高亮的tokens: {selected_tokens}")
        
        if self.test_chat_screen.selected_text_backup:
            print("🎉 Token选择功能测试成功！")
        else:
            print("❌ Token选择功能测试失败！")

def main():
    """主函数"""
    print("🚀 启动Token选择功能测试...")
    print("📱 将打开GUI窗口，测试基于词/短语的选择功能")
    
    # 设置窗口大小
    Window.size = (1400, 900)
    
    # 运行应用
    app = TokenSelectionTestApp()
    app.run()

if __name__ == "__main__":
    main() 