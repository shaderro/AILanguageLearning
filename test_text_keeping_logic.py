"""
文本保持逻辑测试脚本
不依赖GUI，直接测试文本保持的核心逻辑
"""

class MockTextInput:
    """模拟TextInput组件"""
    def __init__(self):
        self.selection_text = ""
        self.focus = False

class MockLabel:
    """模拟Label组件"""
    def __init__(self):
        self.text = ""
        self.color = (0.5, 0.5, 0.5, 1)

class TextKeepingLogicTest:
    """文本保持逻辑测试类"""
    
    def __init__(self):
        self.chat_history = []
        self.selected_text_backup = ""
        self.is_text_selected = False
        self.selection_start = 0
        self.selection_end = 0
        
        # 模拟组件
        self.article_content_widget = MockTextInput()
        self.chat_input = MockTextInput()
        self.selection_label = MockLabel()
        
        # 文章数据
        self.article_title = "Test Article"
        self.article_content = "The internet has revolutionized the way we learn languages."
    
    def _on_chat_input_focus(self, instance, value):
        """聊天输入框焦点事件"""
        if value:  # 获得焦点
            # 在获得焦点前备份当前选中的文本
            current_selection = self.article_content_widget.selection_text
            if current_selection:
                self.selected_text_backup = current_selection
                self.is_text_selected = True
                print(f"🎯 输入框获得焦点，备份选中文本: '{self.selected_text_backup}'")
            elif self.selected_text_backup and self.is_text_selected:
                print(f"🎯 输入框获得焦点，保持之前选中文本: '{self.selected_text_backup}'")
            else:
                print("🎯 输入框获得焦点，没有选中文本")
        else:  # 失去焦点
            print(f"🎯 输入框失去焦点，当前选中文本: '{self.selected_text_backup}'")
    
    def _on_text_selection_change(self, instance, value):
        """文本选择变化事件"""
        if value:  # 有选中的文本
            self.is_text_selected = True
            self.selected_text_backup = value
            print(f"📝 选中文本: '{value}'")
        else:  # 没有选中的文本
            # 检查是否是因为点击输入框导致的清除
            # 如果是，保持之前的选择状态
            if hasattr(self, 'chat_input') and self.chat_input.focus:
                print(f"📝 文本选择被清除（可能是点击输入框），保持之前选择: '{self.selected_text_backup}'")
                # 不清除选择状态，保持之前的备份
            else:
                self.is_text_selected = False
                print("📝 清除文本选择")
        
        # 更新选择状态显示
        self._update_selection_display()
    
    def _update_selection_display(self):
        """更新选择状态显示"""
        # 检查是否有有效的选中文本（当前选择或备份）
        current_selection = self.article_content_widget.selection_text
        has_backup = self.selected_text_backup and self.is_text_selected
        
        if current_selection:
            # 有当前选择
            selected_text = current_selection[:50] + "..." if len(current_selection) > 50 else current_selection
            self.selection_label.text = f'Selected: "{selected_text}"'
            self.selection_label.color = (0.2, 0.6, 1, 1)
            print(f"📝 显示当前选择: '{selected_text}'")
        elif has_backup:
            # 没有当前选择但有备份（比如点击输入框后）
            selected_text = self.selected_text_backup[:50] + "..." if len(self.selected_text_backup) > 50 else self.selected_text_backup
            self.selection_label.text = f'Selected (kept): "{selected_text}"'
            self.selection_label.color = (0.2, 0.8, 0.2, 1)  # 绿色表示保持的选择
            print(f"📝 显示保持的选择: '{selected_text}'")
        else:
            # 没有任何选择
            self.selection_label.text = 'No text selected'
            self.selection_label.color = (0.5, 0.5, 0.5, 1)
            print("📝 没有选中文本")
    
    def _get_selected_text(self):
        """获取当前选中的文本"""
        # 优先返回当前选择，如果没有则返回备份
        if self.article_content_widget.selection_text:
            return self.article_content_widget.selection_text
        elif self.selected_text_backup and self.is_text_selected:
            return self.selected_text_backup
        return ""
    
    def test_text_keeping_scenario(self):
        """测试文本保持场景"""
        print("🧪 开始测试文本保持场景...")
        
        # 步骤1: 选择文本
        print("\n步骤1: 选择文本")
        self.article_content_widget.selection_text = "revolutionized"
        self._on_text_selection_change(None, "revolutionized")
        
        # 步骤2: 点击输入框（模拟获得焦点）
        print("\n步骤2: 点击输入框")
        self.chat_input.focus = True
        self._on_chat_input_focus(self.chat_input, True)
        
        # 步骤3: 模拟文本选择被清除（Kivy的行为）
        print("\n步骤3: 模拟文本选择被清除")
        self.article_content_widget.selection_text = ""
        self._on_text_selection_change(None, "")
        
        # 步骤4: 检查文本是否被保持
        print("\n步骤4: 检查文本保持状态")
        selected_text = self._get_selected_text()
        print(f"✅ 获取的文本: '{selected_text}'")
        
        if selected_text == "revolutionized":
            print("🎉 文本保持功能测试成功！")
            return True
        else:
            print("❌ 文本保持功能测试失败！")
            return False

def main():
    """主函数"""
    print("🚀 启动文本保持逻辑测试...")
    
    # 创建测试实例
    test = TextKeepingLogicTest()
    
    # 运行测试
    success = test.test_text_keeping_scenario()
    
    # 显示最终状态
    print("\n📊 最终状态:")
    print(f"✅ 备份文本: '{test.selected_text_backup}'")
    print(f"✅ 选择状态: {test.is_text_selected}")
    print(f"✅ 当前选择: '{test.article_content_widget.selection_text}'")
    print(f"✅ 显示文本: '{test.selection_label.text}'")
    
    if success:
        print("\n🎉 所有测试通过！文本保持功能正常工作。")
    else:
        print("\n❌ 测试失败！需要进一步调试。")

if __name__ == "__main__":
    main() 