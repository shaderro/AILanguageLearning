"""
文章列表的ViewModel
负责处理文章卡片的数据逻辑
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from data_managers.data_controller import DataController
    from data_managers.data_classes import OriginalText
except ImportError as e:
    print(f"❌ 无法导入数据管理器: {e}")
    # 创建模拟的数据类
    from dataclasses import dataclass
    from typing import List
    
    @dataclass
    class Sentence:
        text_id: int
        sentence_id: int
        sentence_body: str
        grammar_annotations: List[int]
        vocab_annotations: List[int]
    
    @dataclass
    class OriginalText:
        text_id: int
        text_title: str
        text_by_sentence: List[Sentence]
    
    DataController = None


@dataclass
class ArticleCardData:
    """文章卡片的数据模型"""
    text_id: int
    title: str
    word_count: int
    level: str
    progress_percent: int
    is_available: bool = True


class ArticleListViewModel:
    """文章列表的ViewModel"""
    
    def __init__(self):
        """初始化ViewModel"""
        self.data_controller: Optional[DataController] = None
        self.articles: List[ArticleCardData] = []
        self._load_data_controller()
    
    def _load_data_controller(self):
        """加载数据控制器"""
        if DataController is None:
            print("❌ DataController不可用，使用测试数据")
            return
            
        try:
            # DataController需要max_turns参数
            self.data_controller = DataController(max_turns=10)
            
            # 加载数据文件 - 使用正确的相对路径
            data_dir = os.path.join(project_root, "data")
            self.data_controller.load_data(
                grammar_path=os.path.join(data_dir, "grammar_rules.json"),
                vocab_path=os.path.join(data_dir, "vocab_expressions.json"), 
                text_path=os.path.join(data_dir, "original_texts.json"),
                dialogue_record_path=os.path.join(data_dir, "dialogue_record.json"),
                dialogue_history_path=os.path.join(data_dir, "dialogue_history.json")
            )
            print("✅ 数据控制器加载成功")
        except Exception as e:
            print(f"❌ 数据控制器加载失败: {e}")
            self.data_controller = None
    
    def load_articles(self) -> List[ArticleCardData]:
        """加载文章列表数据"""
        self.articles = []
        
        if not self.data_controller:
            # 如果没有数据控制器，返回测试数据
            return self._get_test_articles()
        
        try:
            # 从数据控制器获取所有原始文本对象
            original_texts = self.data_controller.text_manager.list_texts_by_title()
            
            for text in original_texts:
                # 计算单词数（简单估算）
                word_count = self._calculate_word_count(text)
                
                # 确定难度等级
                level = self._determine_level(word_count)
                
                # 计算阅读进度（暂时设为0，后续可以从用户数据获取）
                progress = 0
                
                article_data = ArticleCardData(
                    text_id=text.text_id,
                    title=text.text_title,
                    word_count=word_count,
                    level=level,
                    progress_percent=progress
                )
                
                self.articles.append(article_data)
                print(f"📚 加载文章: {text.text_title} (ID: {text.text_id}, 单词数: {word_count})")
            
            return self.articles
            
        except Exception as e:
            print(f"❌ 加载文章数据失败: {e}")
            return self._get_test_articles()
    
    def _get_text_id_by_title(self, title: str) -> int:
        """根据标题获取文本ID"""
        # 这里需要从数据中查找，暂时返回1
        # 实际实现中应该从text_manager中查找
        return 1
    
    def _calculate_word_count(self, text: OriginalText) -> int:
        """计算文章的单词数"""
        total_words = 0
        for sentence in text.text_by_sentence:
            # 简单的单词计数：按空格分割
            words = sentence.sentence_body.split()
            total_words += len(words)
        return total_words
    
    def _determine_level(self, word_count: int) -> str:
        """根据单词数确定难度等级"""
        if word_count < 50:
            return "Beginner"
        elif word_count < 150:
            return "Intermediate"
        else:
            return "Advanced"
    
    def _get_test_articles(self) -> List[ArticleCardData]:
        """获取测试文章数据"""
        test_articles = [
            ArticleCardData(1, "First Test Text", 45, "Beginner", 0),
            ArticleCardData(2, "Second Test Text", 8, "Beginner", 0),
            ArticleCardData(3, "Test Text", 0, "Beginner", 0),
            ArticleCardData(4, "Test Text", 0, "Beginner", 0)
        ]
        print("📚 使用测试文章数据")
        return test_articles
    
    def get_article_by_id(self, text_id: int) -> Optional[OriginalText]:
        """根据ID获取文章详情"""
        if not self.data_controller:
            return None
        
        try:
            return self.data_controller.get_text_by_id(text_id)
        except Exception as e:
            print(f"❌ 获取文章详情失败: {e}")
            return None
    
    def get_article_by_title(self, title: str) -> Optional[OriginalText]:
        """根据标题获取文章详情"""
        if not self.data_controller:
            return None
        
        try:
            # 根据标题查找文章
            text_titles = self.data_controller.list_texts_by_title()
            if title in text_titles:
                # 这里需要实现根据标题查找ID的逻辑
                # 暂时返回None
                return None
            return None
        except Exception as e:
            print(f"❌ 获取文章详情失败: {e}")
            return None
    
    def refresh_data(self):
        """刷新数据"""
        print("🔄 刷新文章数据...")
        self.load_articles() 