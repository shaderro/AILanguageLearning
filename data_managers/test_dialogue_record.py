import unittest
import tempfile
import os
import json
from data_managers.dialogue_record import DialogueRecordBySentence
from data_managers.data_classes import Sentence


class TestDialogueRecordBySentence(unittest.TestCase):
    
    def setUp(self):
        """测试前的设置"""
        self.dialogue_record = DialogueRecordBySentence()
        self.test_sentence1 = Sentence(text_id=1, sentence_id=1, sentence_body="这是第一句话", grammar_annotations=[], vocab_annotations=[])
        self.test_sentence2 = Sentence(text_id=1, sentence_id=2, sentence_body="这是第二句话", grammar_annotations=[], vocab_annotations=[])
        
    def test_save_all_to_file_and_load(self):
        """测试保存和加载功能"""
        # 添加一些测试数据
        self.dialogue_record.add_user_message(self.test_sentence1, "这句话什么意思？")
        self.dialogue_record.add_ai_response(self.test_sentence1, "这句话的意思是...")
        
        self.dialogue_record.add_user_message(self.test_sentence1, "能举个例子吗？")
        self.dialogue_record.add_ai_response(self.test_sentence1, "当然可以，比如...")
        
        self.dialogue_record.add_user_message(self.test_sentence2, "这句话的语法结构是什么？")
        self.dialogue_record.add_ai_response(self.test_sentence2, "这个句子的语法结构是...")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
        
        try:
            # 测试保存功能
            self.dialogue_record.save_all_to_file(temp_path)
            
            # 验证文件是否被创建
            self.assertTrue(os.path.exists(temp_path))
            
            # 读取文件内容验证
            with open(temp_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # 验证保存的数据结构
            self.assertIsInstance(saved_data, list)
            self.assertEqual(len(saved_data), 3)  # 应该有3条记录
            
            # 验证数据内容
            expected_text_ids = [1, 1, 1]
            expected_sentence_ids = [1, 1, 2]
            expected_user_questions = ["这句话什么意思？", "能举个例子吗？", "这句话的语法结构是什么？"]
            
            for i, record in enumerate(saved_data):
                self.assertEqual(record["text_id"], expected_text_ids[i])
                self.assertEqual(record["sentence_id"], expected_sentence_ids[i])
                self.assertEqual(record["user_question"], expected_user_questions[i])
                self.assertIsNotNone(record["ai_response"])
                self.assertTrue(record["is_learning_related"])
            
            # 测试加载功能
            new_dialogue_record = DialogueRecordBySentence()
            new_dialogue_record.load_from_file(temp_path)
            
            # 验证加载后的数据
            records1 = new_dialogue_record.get_records_by_sentence(self.test_sentence1)
            records2 = new_dialogue_record.get_records_by_sentence(self.test_sentence2)
            
            self.assertEqual(len(records1), 2)  # 第一句话有2条记录
            self.assertEqual(len(records2), 1)  # 第二句话有1条记录
            
            # 验证具体内容
            self.assertEqual(records1[0]["这句话什么意思？"], "这句话的意思是...")
            self.assertEqual(records1[1]["能举个例子吗？"], "当然可以，比如...")
            self.assertEqual(records2[0]["这句话的语法结构是什么？"], "这个句子的语法结构是...")
            
        finally:
            # 保留临时文件供查看
            print(f"📁 测试生成的JSON文件保存在: {temp_path}")
            print(f"📄 文件内容:")
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(content)
            except Exception as e:
                print(f"读取文件失败: {e}")
            # 注释掉删除操作，保留文件
            # if os.path.exists(temp_path):
            #     os.unlink(temp_path)
    
    def test_load_from_nonexistent_file(self):
        """测试加载不存在的文件"""
        nonexistent_path = "/nonexistent/path/file.json"
        
        with self.assertRaises(FileNotFoundError):
            self.dialogue_record.load_from_file(nonexistent_path)
    
    def test_load_from_empty_file(self):
        """测试加载空文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
        
        try:
            # 创建空文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write("")
            
            # 应该不会抛出异常，但会显示警告
            self.dialogue_record.load_from_file(temp_path)
            
            # 验证记录为空
            self.assertEqual(len(self.dialogue_record.records), 0)
            
        finally:
            # 保留临时文件供查看
            print(f"📁 空文件测试的JSON文件保存在: {temp_path}")
            # 注释掉删除操作，保留文件
            # if os.path.exists(temp_path):
            #     os.unlink(temp_path)
    
    def test_load_from_invalid_json(self):
        """测试加载无效的JSON文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
        
        try:
            # 创建无效的JSON文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write("invalid json content")
            
            # 应该不会抛出异常，但会显示错误信息
            self.dialogue_record.load_from_file(temp_path)
            
        finally:
            # 保留临时文件供查看
            print(f"📁 无效JSON测试的文件保存在: {temp_path}")
            print(f"📄 文件内容: invalid json content")
            # 注释掉删除操作，保留文件
            # if os.path.exists(temp_path):
            #     os.unlink(temp_path)
    
    def test_save_and_load_with_missing_ai_response(self):
        """测试保存和加载包含缺失AI回复的记录"""
        # 添加用户消息但不添加AI回复
        self.dialogue_record.add_user_message(self.test_sentence1, "这个问题还没有回答")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
        
        try:
            # 保存
            self.dialogue_record.save_all_to_file(temp_path)
            
            # 加载
            new_dialogue_record = DialogueRecordBySentence()
            new_dialogue_record.load_from_file(temp_path)
            
            # 验证
            records = new_dialogue_record.get_records_by_sentence(self.test_sentence1)
            self.assertEqual(len(records), 1)
            
            # 检查AI回复为None
            for turn in records:
                for user_question, ai_response in turn.items():
                    self.assertEqual(user_question, "这个问题还没有回答")
                    self.assertIsNone(ai_response)
            
        finally:
            # 保留临时文件供查看
            print(f"📁 缺失AI回复测试的JSON文件保存在: {temp_path}")
            print(f"📄 文件内容:")
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(content)
            except Exception as e:
                print(f"读取文件失败: {e}")
            # 注释掉删除操作，保留文件
            # if os.path.exists(temp_path):
            #     os.unlink(temp_path)
    
    def test_save_filtered_to_file(self):
        """测试保存过滤后的数据"""
        # 添加测试数据
        self.dialogue_record.add_user_message(self.test_sentence1, "测试问题")
        self.dialogue_record.add_ai_response(self.test_sentence1, "测试回答")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
        
        try:
            # 保存过滤后的数据
            self.dialogue_record.save_filtered_to_file(temp_path, only_learning_related=True)
            
            # 验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            self.assertEqual(len(saved_data), 1)
            self.assertTrue(saved_data[0]["is_learning_related"])
            
        finally:
            # 保留临时文件供查看
            print(f"📁 过滤数据测试的JSON文件保存在: {temp_path}")
            print(f"📄 文件内容:")
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(content)
            except Exception as e:
                print(f"读取文件失败: {e}")
            # 注释掉删除操作，保留文件
            # if os.path.exists(temp_path):
            #     os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main() 