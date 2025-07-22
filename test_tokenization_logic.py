"""
分词逻辑测试脚本
测试文本分词功能
"""

class TokenizationTest:
    """分词功能测试类"""
    
    def __init__(self):
        self.test_text = "The internet has revolutionized the way we learn languages."
    
    def _tokenize_text(self, text):
        """将文本分词为词/短语"""
        import re
        
        # 使用正则表达式分词
        # 保留标点符号作为单独的token
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        
        # 过滤空token并合并相邻的标点符号
        filtered_tokens = []
        for token in tokens:
            if token.strip():
                filtered_tokens.append(token)
        
        return filtered_tokens
    
    def test_tokenization(self):
        """测试分词功能"""
        print("🧪 开始测试分词功能...")
        print(f"📝 测试文本: '{self.test_text}'")
        
        # 分词
        tokens = self._tokenize_text(self.test_text)
        
        print(f"📝 分词结果: {tokens}")
        print(f"📝 Token数量: {len(tokens)}")
        
        # 验证分词结果
        expected_tokens = ['The', 'internet', 'has', 'revolutionized', 'the', 'way', 'we', 'learn', 'languages', '.']
        
        if tokens == expected_tokens:
            print("🎉 分词功能测试成功！")
            return True
        else:
            print(f"❌ 分词功能测试失败！")
            print(f"   期望: {expected_tokens}")
            print(f"   实际: {tokens}")
            return False
    
    def test_selection_logic(self):
        """测试选择逻辑"""
        print("\n🧪 开始测试选择逻辑...")
        
        # 模拟tokens
        tokens = ['The', 'internet', 'has', 'revolutionized', 'the', 'way', 'we', 'learn', 'languages', '.']
        
        # 模拟选择范围
        selection_start_index = 1  # "internet"
        selection_end_index = 3    # "revolutionized"
        
        # 构造选中的文本
        selected_tokens = []
        for i in range(selection_start_index, selection_end_index + 1):
            if 0 <= i < len(tokens):
                selected_tokens.append(tokens[i])
        
        selected_text = " ".join(selected_tokens)
        
        print(f"📝 选择范围: {selection_start_index} - {selection_end_index}")
        print(f"📝 选中的tokens: {selected_tokens}")
        print(f"📝 构造的文本: '{selected_text}'")
        
        expected_text = "internet has revolutionized"
        
        if selected_text == expected_text:
            print("🎉 选择逻辑测试成功！")
            return True
        else:
            print(f"❌ 选择逻辑测试失败！")
            print(f"   期望: '{expected_text}'")
            print(f"   实际: '{selected_text}'")
            return False
    
    def test_complex_text(self):
        """测试复杂文本分词"""
        print("\n🧪 开始测试复杂文本分词...")
        
        complex_text = "The internet has revolutionized the way we learn languages. With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before."
        
        tokens = self._tokenize_text(complex_text)
        
        print(f"📝 复杂文本: '{complex_text[:50]}...'")
        print(f"📝 分词结果: {tokens}")
        print(f"📝 Token数量: {len(tokens)}")
        
        # 检查是否包含预期的词
        expected_words = ['The', 'internet', 'has', 'revolutionized', 'online', 'platforms', 'mobile', 'applications']
        
        missing_words = []
        for word in expected_words:
            if word not in tokens:
                missing_words.append(word)
        
        if not missing_words:
            print("🎉 复杂文本分词测试成功！")
            return True
        else:
            print(f"❌ 复杂文本分词测试失败！")
            print(f"   缺失的词: {missing_words}")
            return False

def main():
    """主函数"""
    print("🚀 启动分词逻辑测试...")
    
    # 创建测试实例
    test = TokenizationTest()
    
    # 运行测试
    test1_success = test.test_tokenization()
    test2_success = test.test_selection_logic()
    test3_success = test.test_complex_text()
    
    # 总结
    print("\n📊 测试总结:")
    print(f"✅ 基础分词测试: {'通过' if test1_success else '失败'}")
    print(f"✅ 选择逻辑测试: {'通过' if test2_success else '失败'}")
    print(f"✅ 复杂文本测试: {'通过' if test3_success else '失败'}")
    
    if test1_success and test2_success and test3_success:
        print("\n🎉 所有测试通过！分词功能正常工作。")
    else:
        print("\n❌ 部分测试失败！需要进一步调试。")

if __name__ == "__main__":
    main() 