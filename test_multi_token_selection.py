"""
多Token选择功能测试脚本
测试长按拖拽和连续点击选择多个token的功能
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.clock import Clock
from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest

class MultiTokenSelectionTestApp(App):
    """多Token选择功能测试应用"""
    
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
        
        print("\n🎯 多Token选择功能测试说明:")
        print("1. 长按拖拽选择多个词：按住一个词，拖拽到其他词，覆盖的词全选中")
        print("2. 连续点击选择多个词：快速连续点击多个词，同时选中")
        print("3. 点击空白处取消选择：点击词之间的空白区域，清除所有选择")
        print("4. 观察控制台输出，查看选择状态")
        
        return sm
    
    def run_automated_test(self, dt):
        """运行自动测试"""
        print("\n🧪 开始自动测试多Token选择功能...")
        
        # 检查分词结果
        if hasattr(self.test_chat_screen, 'tokens'):
            print(f"📝 分词结果: {self.test_chat_screen.tokens}")
            print(f"📝 Token数量: {len(self.test_chat_screen.tokens)}")
            
            # 测试1：选择单个token
            if len(self.test_chat_screen.token_widgets) > 0:
                first_token = self.test_chat_screen.token_widgets[0]
                print(f"\n🎯 测试1：选择单个token: '{first_token.token_text}'")
                
                # 模拟选择第一个token
                self.test_chat_screen.selection_start_index = first_token.token_index
                self.test_chat_screen.selection_end_index = first_token.token_index
                self.test_chat_screen.selected_indices.add(first_token.token_index)
                self.test_chat_screen._highlight_token(first_token, True)
                self.test_chat_screen._update_selection_from_tokens()
                
                # 检查选择状态
                Clock.schedule_once(self.check_single_selection, 0.5)
        else:
            print("❌ 没有找到tokens，测试失败")
    
    def check_single_selection(self, dt):
        """检查单个选择状态"""
        print("\n📊 检查单个选择状态:")
        print(f"✅ 选中的索引: {sorted(self.test_chat_screen.selected_indices)}")
        print(f"✅ 选中文本: '{self.test_chat_screen.selected_text_backup}'")
        
        if self.test_chat_screen.selected_text_backup == "The":
            print("🎉 单个选择测试成功！")
            
            # 测试2：连续点击选择多个token
            Clock.schedule_once(self.test_continuous_click, 1.0)
        else:
            print("❌ 单个选择测试失败！")
    
    def test_continuous_click(self, dt):
        """测试连续点击选择多个token"""
        print("\n🎯 测试2：连续点击选择多个token")
        
        # 模拟连续点击选择前3个token
        for i in range(3):
            if i < len(self.test_chat_screen.token_widgets):
                token = self.test_chat_screen.token_widgets[i]
                print(f"🎯 连续点击token: '{token.token_text}'")
                self.test_chat_screen.selected_indices.add(token.token_index)
                self.test_chat_screen._highlight_token(token, True)
        
        self.test_chat_screen._update_selection_from_tokens()
        
        # 检查选择状态
        Clock.schedule_once(self.check_continuous_selection, 0.5)
    
    def check_continuous_selection(self, dt):
        """检查连续选择状态"""
        print("\n📊 检查连续选择状态:")
        print(f"✅ 选中的索引: {sorted(self.test_chat_screen.selected_indices)}")
        print(f"✅ 选中文本: '{self.test_chat_screen.selected_text_backup}'")
        
        expected_text = "The internet has"
        if self.test_chat_screen.selected_text_backup == expected_text:
            print("🎉 连续选择测试成功！")
            
            # 测试3：点击空白处取消选择
            Clock.schedule_once(self.test_clear_selection, 1.0)
        else:
            print(f"❌ 连续选择测试失败！期望: '{expected_text}'")
    
    def test_clear_selection(self, dt):
        """测试点击空白处取消选择"""
        print("\n🎯 测试3：点击空白处取消选择")
        
        # 模拟点击空白处
        self.test_chat_screen._clear_all_selections()
        self.test_chat_screen._update_selection_from_tokens()
        
        # 检查选择状态
        Clock.schedule_once(self.check_clear_selection, 0.5)
    
    def check_clear_selection(self, dt):
        """检查清除选择状态"""
        print("\n📊 检查清除选择状态:")
        print(f"✅ 选中的索引: {sorted(self.test_chat_screen.selected_indices)}")
        print(f"✅ 选中文本: '{self.test_chat_screen.selected_text_backup}'")
        
        if not self.test_chat_screen.selected_indices and not self.test_chat_screen.selected_text_backup:
            print("🎉 清除选择测试成功！")
            print("\n🎉 所有多Token选择功能测试通过！")
        else:
            print("❌ 清除选择测试失败！")

def main():
    """主函数"""
    print("🚀 启动多Token选择功能测试...")
    print("📱 将打开GUI窗口，测试多Token选择功能")
    
    # 设置窗口大小
    Window.size = (1400, 900)
    
    # 运行应用
    app = MultiTokenSelectionTestApp()
    app.run()

if __name__ == "__main__":
    main() 