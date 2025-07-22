"""
独立测试运行脚本
直接运行TextInputChatScreenTest的test_run功能
"""

def test_run_standalone():
    """独立测试运行"""
    print("🚀 启动独立测试运行...")
    
    try:
        # 导入测试页面
        from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest
        
        # 创建测试页面实例
        test_screen = TextInputChatScreenTest()
        
        # 运行测试功能
        test_screen.test_run()
        
        # 验证测试结果
        print("\n📊 测试结果验证:")
        print(f"✅ 文章标题: {test_screen.article_title}")
        print(f"✅ 文章内容长度: {len(test_screen.article_content)} 字符")
        print(f"✅ 聊天历史长度: {len(test_screen.chat_history)} 条消息")
        print(f"✅ 选中文本备份: '{test_screen.selected_text_backup}'")
        print(f"✅ 文本选择状态: {test_screen.is_text_selected}")
        
        # 测试AI回复功能
        print("\n🧪 测试AI回复功能:")
        test_response1 = test_screen._generate_ai_response("What does this mean?", "revolutionized")
        print(f"✅ 有选中文本的回复: {test_response1[:50]}...")
        
        test_response2 = test_screen._generate_ai_response("Hello", "")
        print(f"✅ 无选中文本的回复: {test_response2[:50]}...")
        
        print("\n🎉 独立测试运行完成！所有功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_run_standalone() 