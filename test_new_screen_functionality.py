"""
测试新页面功能
验证TextInputChatScreenTest的基本功能
"""

def test_new_screen_import():
    """测试新页面导入"""
    try:
        from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest
        print("✅ 成功导入 TextInputChatScreenTest")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_screen_creation():
    """测试页面创建"""
    try:
        from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest
        
        # 创建测试页面
        test_screen = TextInputChatScreenTest()
        print("✅ 成功创建 TextInputChatScreenTest 实例")
        
        # 检查基本属性
        assert hasattr(test_screen, 'article_title'), "缺少 article_title 属性"
        assert hasattr(test_screen, 'article_content'), "缺少 article_content 属性"
        assert hasattr(test_screen, 'chat_history'), "缺少 chat_history 属性"
        assert hasattr(test_screen, 'selected_text_backup'), "缺少 selected_text_backup 属性"
        
        print("✅ 基本属性检查通过")
        return True
    except Exception as e:
        print(f"❌ 页面创建失败: {e}")
        return False

def test_article_setting():
    """测试文章设置功能"""
    try:
        from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest
        
        # 创建测试页面
        test_screen = TextInputChatScreenTest()
        
        # 创建模拟文章数据
        class MockArticleData:
            def __init__(self):
                self.text_title = "Test Article Title"
                self.text_by_sentence = [
                    type('MockSentence', (), {'sentence_body': 'This is the first sentence.'})(),
                    type('MockSentence', (), {'sentence_body': 'This is the second sentence.'})()
                ]
        
        # 设置文章
        article_data = MockArticleData()
        test_screen.set_article(article_data)
        
        # 验证设置结果
        assert test_screen.article_title == "Test Article Title", "文章标题设置失败"
        assert "This is the first sentence." in test_screen.article_content, "文章内容设置失败"
        
        print("✅ 文章设置功能正常")
        return True
    except Exception as e:
        print(f"❌ 文章设置测试失败: {e}")
        return False

def test_text_selection():
    """测试文本选择功能"""
    try:
        from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest
        
        # 创建测试页面
        test_screen = TextInputChatScreenTest()
        
        # 测试文本选择变化
        test_screen._on_text_selection_change(None, "selected text")
        assert test_screen.is_text_selected == True, "文本选择状态设置失败"
        assert test_screen.selected_text_backup == "selected text", "选中文本备份失败"
        
        # 测试清除选择
        test_screen._on_text_selection_change(None, "")
        assert test_screen.is_text_selected == False, "文本选择清除失败"
        
        print("✅ 文本选择功能正常")
        return True
    except Exception as e:
        print(f"❌ 文本选择测试失败: {e}")
        return False

def test_ai_response():
    """测试AI回复功能"""
    try:
        from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest
        
        # 创建测试页面
        test_screen = TextInputChatScreenTest()
        
        # 测试有选中文本的回复
        response1 = test_screen._generate_ai_response("What does this mean?", "revolutionized")
        assert "revolutionized" in response1, "AI回复应该包含选中的文本"
        
        # 测试没有选中文本的回复
        response2 = test_screen._generate_ai_response("Hello", "")
        assert "Hello" in response2 or "你好" in response2, "AI回复应该包含问候语"
        
        print("✅ AI回复功能正常")
        return True
    except Exception as e:
        print(f"❌ AI回复测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始测试新页面功能...")
    
    tests = [
        ("页面导入", test_new_screen_import),
        ("页面创建", test_screen_creation),
        ("文章设置", test_article_setting),
        ("文本选择", test_text_selection),
        ("AI回复", test_ai_response),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📝 测试: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} 测试失败")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！新页面功能正常")
    else:
        print("⚠️ 部分测试失败，需要检查")

if __name__ == "__main__":
    main() 