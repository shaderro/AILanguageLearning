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
            # 如果没有数据控制器，从JSON文件直接加载
            return self._load_articles_from_json()
        
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
            return self._load_articles_from_json()
    
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
    
    def _load_articles_from_json(self) -> List[ArticleCardData]:
        """从JSON文件加载文章数据"""
        import json
        import os
        
        try:
            # 构建JSON文件路径
            json_path = os.path.join(project_root, "data", "original_texts.json")
            
            if not os.path.exists(json_path):
                print(f"❌ 文章数据文件不存在: {json_path}")
                return self._get_test_articles()
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = []
            for text_id_str, text_data in data.items():
                text_id = int(text_id_str)
                title = text_data.get("text_title", f"Article {text_id}")
                sentences = text_data.get("text_by_sentence", [])
                
                # 计算单词数
                word_count = sum(len(sentence.get("sentence_body", "").split()) for sentence in sentences)
                
                # 确定难度等级
                level = self._determine_level(word_count)
                
                # 计算阅读进度（暂时设为0）
                progress = 0
                
                article_data = ArticleCardData(
                    text_id=text_id,
                    title=title,
                    word_count=word_count,
                    level=level,
                    progress_percent=progress
                )
                
                articles.append(article_data)
                print(f"📚 从JSON加载文章: {title} (ID: {text_id}, 单词数: {word_count})")
            
            return articles
            
        except Exception as e:
            print(f"❌ 从JSON加载文章失败: {e}")
            return self._get_test_articles()
    
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
    
    def _get_article_by_id_from_json(self, text_id: int) -> Optional[OriginalText]:
        """从JSON文件根据ID获取文章详情"""
        import json
        import os
        
        try:
            # 构建JSON文件路径
            json_path = os.path.join(project_root, "data", "original_texts.json")
            
            if not os.path.exists(json_path):
                print(f"❌ 文章数据文件不存在: {json_path}")
                return None
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 查找指定ID的文章
            text_id_str = str(text_id)
            if text_id_str not in data:
                print(f"❌ 文章ID {text_id} 不存在")
                return None
            
            text_data = data[text_id_str]
            
            # 构建OriginalText对象
            sentences = []
            for sentence_data in text_data.get("text_by_sentence", []):
                sentence = Sentence(
                    text_id=sentence_data.get("text_id", text_id),
                    sentence_id=sentence_data.get("sentence_id", 0),
                    sentence_body=sentence_data.get("sentence_body", ""),
                    grammar_annotations=sentence_data.get("grammar_annotations", []),
                    vocab_annotations=sentence_data.get("vocab_annotations", [])
                )
                sentences.append(sentence)
            
            original_text = OriginalText(
                text_id=text_data.get("text_id", text_id),
                text_title=text_data.get("text_title", f"Article {text_id}"),
                text_by_sentence=sentences
            )
            
            print(f"📖 从JSON加载文章详情: {original_text.text_title} (ID: {text_id})")
            return original_text
            
        except Exception as e:
            print(f"❌ 从JSON获取文章详情失败: {e}")
            return None
    
    def _get_test_article_by_id(self, text_id: int) -> Optional[OriginalText]:
        """根据ID获取测试文章详情"""
        test_articles = {
            1: OriginalText(
                text_id=1,
                text_title="First Test Text",
                text_by_sentence=[
                    Sentence(1, 1, "The Internet and Language Learning", [], []),
                    Sentence(1, 2, "The internet has revolutionized the way we learn languages.", [], []),
                    Sentence(1, 3, "With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.", [], []),
                    Sentence(1, 4, "Online language learning platforms offer a variety of features that traditional classroom settings cannot provide.", [], []),
                    Sentence(1, 5, "These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.", [], [])
                ]
            ),
            2: OriginalText(
                text_id=2,
                text_title="Second Test Text",
                text_by_sentence=[
                    Sentence(2, 1, "Artificial Intelligence in Education", [], []),
                    Sentence(2, 2, "AI is transforming how we teach and learn.", [], []),
                    Sentence(2, 3, "Machine learning algorithms can personalize education for each student.", [], []),
                    Sentence(2, 4, "This technology helps identify learning gaps and provides targeted support.", [], [])
                ]
            ),
            3: OriginalText(
                text_id=3,
                text_title="Test Text",
                text_by_sentence=[
                    Sentence(3, 1, "Climate Change and Sustainability", [], []),
                    Sentence(3, 2, "Climate change is one of the most pressing issues of our time.", [], []),
                    Sentence(3, 3, "We must take action to reduce carbon emissions and protect our planet.", [], [])
                ]
            ),
            4: OriginalText(
                text_id=4,
                text_title="Test Text",
                text_by_sentence=[
                    Sentence(4, 1, "The Future of Technology", [], []),
                    Sentence(4, 2, "Technology continues to evolve at an unprecedented pace.", [], []),
                    Sentence(4, 3, "From artificial intelligence to renewable energy, innovation drives progress.", [], [])
                ]
            )
        }
        
        return test_articles.get(text_id)
    
    def get_article_by_id(self, text_id: int) -> Optional[OriginalText]:
        """根据ID获取文章详情"""
        if not self.data_controller:
            # 从JSON文件加载文章详情
            return self._get_article_by_id_from_json(text_id)
        
        try:
            return self.data_controller.get_text_by_id(text_id)
        except Exception as e:
            print(f"❌ 获取文章详情失败: {e}")
            return self._get_article_by_id_from_json(text_id)
    
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