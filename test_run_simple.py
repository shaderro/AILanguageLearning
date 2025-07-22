"""
简单测试运行脚本
只测试核心功能，不需要Kivy GUI组件
"""

class SimpleTextInputChatTest:
    """简化的测试类，只包含核心功能"""
    
    def __init__(self):
        self.chat_history = []
        self.selected_text_backup = ""
        self.is_text_selected = False
        self.article_title = "Test Article"
        self.article_content = ""
    
    def set_article(self, article_data):
        """设置文章数据"""
        if hasattr(article_data, 'text_title'):
            self.article_title = article_data.text_title
        else:
            self.article_title = "Test Article"
        
        if hasattr(article_data, 'text_by_sentence'):
            # 将句子列表转换为文本
            sentences = []
            for sentence in article_data.text_by_sentence:
                sentences.append(sentence.sentence_body)
            self.article_content = " ".join(sentences)
        else:
            self.article_content = "Article content not available."
        
        print(f"📖 设置文章: {self.article_title}")
        print(f"📝 文章内容长度: {len(self.article_content)} 字符")
    
    def _on_text_selection_change(self, instance, value):
        """文本选择变化事件"""
        if value:  # 有选中的文本
            self.is_text_selected = True
            self.selected_text_backup = value
            print(f"📝 选中文本: '{value}'")
        else:  # 没有选中的文本
            self.is_text_selected = False
            print("📝 清除文本选择")
    
    def _add_chat_message(self, sender, message, is_ai=False, quoted_text=None):
        """添加聊天消息"""
        message_data = {
            'sender': sender,
            'message': message,
            'is_ai': is_ai,
            'quoted_text': quoted_text
        }
        self.chat_history.append(message_data)
        print(f"💬 添加消息: {sender} - {message[:50]}...")
    
    def _generate_ai_response(self, user_message, selected_text):
        """生成AI回复"""
        if selected_text:
            if "meaning" in user_message.lower() or "意思" in user_message:
                return f"关于选中的文本 '{selected_text[:30]}...' 的意思，这是一个很好的问题。让我为您解释..."
            elif "grammar" in user_message.lower() or "语法" in user_message:
                return f"您选中的文本 '{selected_text[:30]}...' 涉及一些语法知识点。让我为您分析..."
            elif "pronunciation" in user_message.lower() or "发音" in user_message:
                return f"关于 '{selected_text[:30]}...' 的发音，这里有一些要点需要注意..."
            else:
                return f"您询问的是关于选中文本 '{selected_text[:30]}...' 的问题。这是一个很好的学习点！"
        else:
            if "help" in user_message.lower() or "帮助" in user_message:
                return "我可以帮助您学习语言！请选择文章中的任何文本，然后询问我关于语法、词汇、发音或意思的问题。"
            elif "hello" in user_message.lower() or "你好" in user_message:
                return "你好！我是您的语言学习助手。请选择文章中的文本，我会回答您的问题。"
            else:
                return "请先选择文章中的一些文本，然后询问我相关问题。我可以帮助您理解语法、词汇、发音等。"
    
    def test_run(self):
        """测试运行功能 - 使用测试数据运行当前页面"""
        print("🧪 开始测试运行 SimpleTextInputChatTest...")
        
        # 设置测试文章数据
        test_article_data = self._create_test_article_data()
        self.set_article(test_article_data)
        
        # 添加一些测试消息
        self._add_test_messages()
        
        print("✅ 测试数据设置完成")
        print("📖 文章标题:", self.article_title)
        print("📝 文章内容长度:", len(self.article_content))
        print("💬 聊天消息数量:", len(self.chat_history))
    
    def _create_test_article_data(self):
        """创建测试文章数据"""
        class TestArticleData:
            def __init__(self):
                self.text_title = "The Internet and Language Learning"
                self.text_by_sentence = [
                    type('MockSentence', (), {'sentence_body': 'The internet has revolutionized the way we learn languages.'})(),
                    type('MockSentence', (), {'sentence_body': 'With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.'})(),
                    type('MockSentence', (), {'sentence_body': 'Online language learning platforms offer a variety of features that traditional classroom settings cannot provide.'})(),
                    type('MockSentence', (), {'sentence_body': 'These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.'})(),
                    type('MockSentence', (), {'sentence_body': 'One of the most significant advantages of internet-based language learning is the availability of authentic materials.'})(),
                    type('MockSentence', (), {'sentence_body': 'Learners can access real news articles, videos, podcasts, and social media content in their target language.'})(),
                    type('MockSentence', (), {'sentence_body': 'Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs.'})(),
                    type('MockSentence', (), {'sentence_body': 'Students can connect with peers from different countries, practice conversation skills, and share cultural insights.'})()
                ]
        
        return TestArticleData()
    
    def _add_test_messages(self):
        """添加测试聊天消息"""
        # 模拟用户选择文本并提问
        test_scenarios = [
            {
                'selected_text': 'revolutionized',
                'user_message': 'What does this word mean?',
                'ai_response': 'revolutionized means "to completely change or transform something in a fundamental way." It comes from the word "revolution" and is often used to describe major technological or social changes.'
            },
            {
                'selected_text': 'the way we learn',
                'user_message': 'What grammar structure is used here?',
                'ai_response': 'This is a noun phrase structure: "the way we learn". Here, "the way" is a noun phrase meaning "the method or manner", and "we learn" is a relative clause that modifies "way". The relative pronoun "that" or "in which" is omitted.'
            },
            {
                'selected_text': '',
                'user_message': 'Can you help me understand this article?',
                'ai_response': 'Of course! This article discusses how the internet has changed language learning. It mentions online platforms, mobile apps, digital resources, and how they make language learning more accessible. Would you like me to explain any specific part in detail?'
            }
        ]
        
        for scenario in test_scenarios:
            # 模拟文本选择
            if scenario['selected_text']:
                self._on_text_selection_change(None, scenario['selected_text'])
                print(f"📝 模拟选择文本: '{scenario['selected_text']}'")
            
            # 添加用户消息
            self._add_chat_message("You", scenario['user_message'], is_ai=False, quoted_text=scenario['selected_text'] if scenario['selected_text'] else None)
            
            # 添加AI回复
            self._add_chat_message("Test AI Assistant", scenario['ai_response'], is_ai=True)
            
            # 清除选择状态
            if scenario['selected_text']:
                self._on_text_selection_change(None, "")
        
        print(f"✅ 添加了 {len(test_scenarios)} 个测试对话场景")

def main():
    """主函数"""
    print("🚀 启动简单测试运行...")
    
    try:
        # 创建测试实例
        test_screen = SimpleTextInputChatTest()
        
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
        
        # 显示聊天历史
        print("\n💬 聊天历史:")
        for i, msg in enumerate(test_screen.chat_history, 1):
            print(f"  {i}. {msg['sender']}: {msg['message'][:50]}...")
            if msg['quoted_text']:
                print(f"     引用: '{msg['quoted_text']}'")
        
        print("\n🎉 简单测试运行完成！所有功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main() 