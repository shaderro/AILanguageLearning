"""
文本输入聊天屏幕的ViewModel
继承BaseViewModel，实现聊天相关的业务逻辑
"""

from kivy.properties import StringProperty, ListProperty, BooleanProperty
from .base_viewmodel import BaseViewModel
from typing import Dict, Any, Optional, List

class TextInputChatViewModel(BaseViewModel):
    """文本输入聊天屏幕的ViewModel"""
    
    # 数据属性
    article_title = StringProperty('Article: The Internet and Language Learning')
    article_content = StringProperty('')
    selected_text = StringProperty('')
    selected_text_backup = StringProperty('')
    is_text_selected = BooleanProperty(False)
    chat_messages = ListProperty([])
    current_input = StringProperty('')
    
    # UI状态属性
    selection_start = 0
    selection_end = 0
    
    def __init__(self, data_binding_service=None, **kwargs):
        super().__init__(name="text_input_chat", data_binding_service=data_binding_service, **kwargs)
    
    def on_initialize(self):
        """实现抽象方法：初始化ViewModel"""
        self._setup_default_content()
        self._setup_data_bindings()
    
    def _setup_default_content(self):
        """设置默认的文章内容"""
        self.article_content = """The Internet and Language Learning

The internet has revolutionized the way we learn languages. With the advent of online platforms, mobile applications, and digital resources, language learning has become more accessible than ever before.

Online language learning platforms offer a variety of features that traditional classroom settings cannot provide. These include interactive exercises, real-time feedback, personalized learning paths, and access to native speakers from around the world.

One of the most significant advantages of internet-based language learning is the availability of authentic materials. Learners can access real news articles, videos, podcasts, and social media content in their target language.

Furthermore, the internet facilitates collaborative learning through online communities and language exchange programs. Students can connect with peers from different countries, practice conversation skills, and share cultural insights."""
        
        # 添加欢迎消息
        self.add_chat_message("AI Assistant", "Hello! I'm here to help you with language learning. You can select any text from the article and ask me questions about it.", is_ai=True)
    
    def _setup_data_bindings(self):
        """设置数据绑定"""
        if self.data_binding_service:
            # 绑定文章数据
            self.bind_to_data_service("article_content", "article_content")
            self.bind_to_data_service("article_title", "article_title")
            # 绑定聊天消息
            self.bind_to_data_service("chat_messages", "chat_messages")
    
    def update_text_selection(self, selected_text: str, start_pos: int, end_pos: int):
        """更新文本选择状态"""
        self.selected_text = selected_text
        self.selection_start = start_pos
        self.selection_end = end_pos
        self.is_text_selected = bool(selected_text)
        print(f"TextInputChatViewModel: 文本选择更新 - '{selected_text[:30]}...' (位置: {start_pos}-{end_pos})")
    
    def backup_selected_text(self):
        """备份选中的文本"""
        if self.selected_text:
            self.selected_text_backup = self.selected_text
            print(f"TextInputChatViewModel: 备份选中文本 - '{self.selected_text_backup[:30]}...'")
    
    def clear_text_selection(self):
        """清除文本选择"""
        self.selected_text = ''
        self.selected_text_backup = ''
        self.is_text_selected = False
        self.selection_start = 0
        self.selection_end = 0
        print("TextInputChatViewModel: 清除文本选择")
    
    def get_selected_text(self) -> str:
        """获取当前选中的文本"""
        # 优先返回当前选择，如果没有则返回备份
        if self.selected_text:
            return self.selected_text
        elif self.selected_text_backup and self.is_text_selected:
            return self.selected_text_backup
        return ""
    
    def add_chat_message(self, sender: str, message: str, is_ai: bool = False, quoted_text: Optional[str] = None):
        """添加聊天消息"""
        message_data = {
            'sender': sender,
            'message': message,
            'is_ai': is_ai,
            'quoted_text': quoted_text,
            'timestamp': self._get_current_timestamp()
        }
        self.chat_messages.append(message_data)
        print(f"TextInputChatViewModel: 添加消息 - {sender}: {message[:30]}...")
    
    def send_message(self, message: str) -> Optional[str]:
        """发送消息"""
        if not message.strip():
            return None
        
        # 获取选中的文本
        selected_text = self.get_selected_text()
        
        # 添加用户消息
        self.add_chat_message("You", message, is_ai=False, quoted_text=selected_text)
        
        # 生成AI回复
        ai_response = self._generate_ai_response(message, selected_text)
        self.add_chat_message("AI Assistant", ai_response, is_ai=True)
        
        # 清空输入
        self.current_input = ''
        
        return ai_response
    
    def _generate_ai_response(self, user_message: str, selected_text: str) -> str:
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
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def load_article_from_data(self, article_data: Dict[str, Any]):
        """从数据源加载文章"""
        if article_data:
            self.article_title = article_data.get('title', 'Article')
            self.article_content = article_data.get('content', '')
            print(f"TextInputChatViewModel: 加载文章 - {self.article_title}")
    
    def save_chat_history(self) -> List[Dict[str, Any]]:
        """保存聊天历史"""
        # 这里可以连接到数据管理器保存聊天记录
        print(f"TextInputChatViewModel: 保存聊天历史 - {len(self.chat_messages)} 条消息")
        return self.chat_messages
    
    def on_before_destroy(self):
        """销毁前的回调"""
        # 保存聊天历史
        if self.data_binding_service:
            self.data_binding_service.save_chat_history(self.chat_messages)
        print("TextInputChatViewModel: 保存聊天历史并准备销毁")
    
    def validate_data(self, data: Any) -> bool:
        """验证数据（重写基类方法）"""
        if isinstance(data, str):
            return len(data.strip()) > 0
        elif isinstance(data, list):
            return len(data) > 0
        return super().validate_data(data)
    
    def transform_data(self, data: Any, transform_type: str) -> Any:
        """转换数据（重写基类方法）"""
        if transform_type == "article_content" and isinstance(data, str):
            # 对文章内容进行特殊处理
            return data.strip()
        elif transform_type == "chat_messages" and isinstance(data, list):
            # 对聊天消息进行特殊处理
            return [msg for msg in data if isinstance(msg, dict) and 'message' in msg]
        return super().transform_data(data, transform_type) 