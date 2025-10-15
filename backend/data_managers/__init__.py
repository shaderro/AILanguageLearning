"""
数据管理器模块

提供多个Manager的两种实现：
1. JSON版本 (旧版本) - 基于 JSON 文件存储
   - 适用于：现有前端、旧接口
   - 逐步淘汰中
   
2. DB版本 (新版本) - 基于数据库存储
   - 适用于：新接口、AI Assistants（需要数据库）
   - 推荐使用

使用示例：

    # Vocab Manager
    from backend.data_managers import VocabManagerDB
    from database_system.database_manager import DatabaseManager
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    vocab_manager = VocabManagerDB(session)
    
    # Grammar Manager
    from backend.data_managers import GrammarRuleManagerDB
    grammar_manager = GrammarRuleManagerDB(session)

迁移计划：
    阶段1（当前）：默认 = JSON，可选 DB
    阶段2：默认 = DB，保留 JSON
    阶段3：只保留 DB
"""

# ==================== Vocab Manager ====================

# 旧版本：基于 JSON 文件
from .vocab_manager import VocabManager as VocabManagerJSON

# 新版本：基于数据库
from .vocab_manager_db import VocabManager as VocabManagerDB

# 默认使用旧版本（保持向后兼容）
VocabManager = VocabManagerJSON


# ==================== Grammar Manager ====================

# 旧版本：基于 JSON 文件
from .grammar_rule_manager import GrammarRuleManager as GrammarRuleManagerJSON

# 新版本：基于数据库
from .grammar_rule_manager_db import GrammarRuleManager as GrammarRuleManagerDB

# 默认使用旧版本（保持向后兼容）
GrammarRuleManager = GrammarRuleManagerJSON


# ==================== OriginalText Manager ====================

# 旧版本：基于 JSON 文件
from .original_text_manager import OriginalTextManager as OriginalTextManagerJSON

# 新版本：基于数据库
from .original_text_manager_db import OriginalTextManager as OriginalTextManagerDB

# 默认使用旧版本（保持向后兼容）
OriginalTextManager = OriginalTextManagerJSON


# ==================== 公开接口 ====================

__all__ = [
    # Vocab Managers
    'VocabManager',        # 默认版本（JSON）
    'VocabManagerJSON',    # 旧版本：JSON 文件存储
    'VocabManagerDB',      # 新版本：数据库存储（推荐）
    
    # Grammar Managers
    'GrammarRuleManager',     # 默认版本（JSON）
    'GrammarRuleManagerJSON', # 旧版本：JSON 文件存储
    'GrammarRuleManagerDB',   # 新版本：数据库存储（推荐）
    
    # OriginalText Managers
    'OriginalTextManager',      # 默认版本（JSON）
    'OriginalTextManagerJSON',  # 旧版本：JSON 文件存储
    'OriginalTextManagerDB',    # 新版本：数据库存储（推荐）
]


# ==================== 版本信息 ====================

def get_vocab_manager_info():
    """
    获取 VocabManager 版本信息
    
    返回:
        dict: 包含版本信息
    """
    return {
        'default': 'VocabManagerJSON',
        'available_versions': {
            'VocabManagerJSON': {
                'storage': 'JSON 文件',
                'status': '稳定，逐步淘汰',
                'requires': 'use_new_structure参数'
            },
            'VocabManagerDB': {
                'storage': '数据库（SQLAlchemy）',
                'status': '开发中，推荐使用',
                'requires': 'Session对象'
            }
        },
        'migration_stage': 1,
        'migration_plan': [
            '阶段1: 默认=JSON，可选DB（当前）',
            '阶段2: 默认=DB，保留JSON',
            '阶段3: 只保留DB'
        ]
    }


# ==================== 使用提示 ====================

# 如果直接运行此模块，显示版本信息
if __name__ == '__main__':
    import json
    info = get_vocab_manager_info()
    print("VocabManager 版本信息：")
    print(json.dumps(info, indent=2, ensure_ascii=False))