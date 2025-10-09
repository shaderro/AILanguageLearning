"""
数据管理器模块

提供两种 VocabManager 实现：
1. VocabManagerJSON (旧版本) - 基于 JSON 文件存储
   - 适用于：现有前端、旧接口
   - 逐步淘汰中
   
2. VocabManagerDB (新版本) - 基于数据库存储
   - 适用于：新接口、AI Assistants（需要数据库）
   - 推荐使用

使用示例：

    # 方式1：使用默认版本（目前是旧版本，保持兼容）
    from backend.data_managers import VocabManager
    vocab_manager = VocabManager(use_new_structure=True)  # JSON 版本
    
    # 方式2：显式使用旧版本
    from backend.data_managers import VocabManagerJSON
    vocab_manager = VocabManagerJSON()
    
    # 方式3：显式使用新版本（推荐）
    from backend.data_managers import VocabManagerDB
    from database_system.database_manager import DatabaseManager
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    vocab_manager = VocabManagerDB(session)  # 数据库版本

迁移计划：
    阶段1（当前）：默认 = VocabManagerJSON，可选 VocabManagerDB
    阶段2：默认 = VocabManagerDB，保留 VocabManagerJSON
    阶段3：只保留 VocabManagerDB
"""

# ==================== 导入两个版本 ====================

# 旧版本：基于 JSON 文件
from .vocab_manager import VocabManager as VocabManagerJSON

# 新版本：基于数据库
from .vocab_manager_db import VocabManager as VocabManagerDB


# ==================== 默认导出 ====================

# 默认使用旧版本（保持向后兼容）
# 前端和现有代码可以继续使用 VocabManager，不会受影响
VocabManager = VocabManagerJSON


# ==================== 公开接口 ====================

__all__ = [
    # 默认版本（当前是旧版本）
    'VocabManager',
    
    # 显式版本（可以明确选择）
    'VocabManagerJSON',    # 旧版本：JSON 文件存储
    'VocabManagerDB',      # 新版本：数据库存储（推荐）
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