"""
文本保持功能测试脚本
专门测试选择文本后点击输入框时文本是否被保持
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.clock import Clock
from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest

class TextKeepingTestApp(App):
    """文本保持功能测试应用"""
    
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
        
        print("\n🎯 文本保持功能测试说明:")
        print("1. 程序会自动模拟以下操作:")
        print("   - 选择文章中的文本")
        print("   - 点击输入框")
        print("   - 验证文本是否被保持")
        print("2. 观察控制台输出，查看文本保持状态")
        print("3. 观察UI中的选中文本显示")
        
        return sm
    
    def run_automated_test(self, dt):
        """运行自动测试"""
        print("\n🧪 开始自动测试文本保持功能...")
        
        # 模拟选择文本
        test_text = "revolutionized"
        print(f"📝 模拟选择文本: '{test_text}'")
        
        # 手动触发文本选择事件
        self.test_chat_screen._on_text_selection_change(None, test_text)
        
        # 等待一下
        Clock.schedule_once(self.simulate_input_focus, 1.0)
    
    def simulate_input_focus(self, dt):
        """模拟输入框获得焦点"""
        print("🎯 模拟点击输入框...")
        
        # 手动触发输入框焦点事件
        self.test_chat_screen._on_chat_input_focus(self.test_chat_screen.chat_input, True)
        
        # 检查文本是否被保持
        Clock.schedule_once(self.check_text_keeping, 0.5)
    
    def check_text_keeping(self, dt):
        """检查文本保持状态"""
        print("\n📊 检查文本保持状态:")
        print(f"✅ 备份文本: '{self.test_chat_screen.selected_text_backup}'")
        print(f"✅ 选择状态: {self.test_chat_screen.is_text_selected}")
        print(f"✅ 当前选择: '{self.test_chat_screen.article_content_widget.selection_text}'")
        
        # 获取选中的文本
        selected_text = self.test_chat_screen._get_selected_text()
        print(f"✅ 获取的文本: '{selected_text}'")
        
        if selected_text == "revolutionized":
            print("🎉 文本保持功能测试成功！")
        else:
            print("❌ 文本保持功能测试失败！")
        
        # 模拟发送消息
        Clock.schedule_once(self.simulate_send_message, 1.0)
    
    def simulate_send_message(self, dt):
        """模拟发送消息"""
        print("\n💬 模拟发送消息...")
        
        # 设置输入框文本
        self.test_chat_screen.chat_input.text = "What does this word mean?"
        
        # 发送消息
        self.test_chat_screen._on_send_message()
        
        print("✅ 消息发送完成，检查聊天历史...")
        print(f"✅ 聊天消息数量: {len(self.test_chat_screen.chat_history)}")

def main():
    """主函数"""
    print("🚀 启动文本保持功能测试...")
    print("📱 将打开GUI窗口，自动测试文本保持功能")
    
    # 设置窗口大小
    Window.size = (1400, 900)
    
    # 运行应用
    app = TextKeepingTestApp()
    app.run()

if __name__ == "__main__":
    main() 