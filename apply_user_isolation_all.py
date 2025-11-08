"""
一键为 Grammar 和 Text API 添加用户认证和数据隔离
"""
import re

def add_auth_import(file_path):
    """添加认证相关的导入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已导入
    if 'from backend.api.auth_routes import get_current_user' in content:
        print(f"  ⏭️  {file_path} 已包含认证导入")
        return content
    
    # 在 DatabaseManager 导入后添加
    if 'from database_system.database_manager import DatabaseManager' in content:
        content = content.replace(
            'from database_system.database_manager import DatabaseManager',
            '''from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User, GrammarRule, OriginalText

# 导入认证依赖
from backend.api.auth_routes import get_current_user'''
        )
        print(f"  ✅ {file_path} 添加认证导入")
    
    return content

def add_user_param_to_endpoint(content, endpoint_pattern):
    """为端点添加 current_user 参数"""
    # 查找端点定义
    pattern = rf'(@router\.(get|post|put|delete)\([^)]+\)\s+async def {endpoint_pattern}\([^)]+)(session: Session = Depends\(get_db_session\))'
    
    def replacer(match):
        prefix = match.group(1)
        session_param = match.group(3)
        
        # 检查是否已有 current_user
        if 'current_user' in prefix:
            return match.group(0)
        
        # 添加 current_user 参数
        return f"{prefix}{session_param},\n    current_user: User = Depends(get_current_user)"
    
    new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    return new_content

# 处理 grammar_routes.py
print("\n" + "="*60)
print("修改 backend/api/grammar_routes.py")
print("="*60)

grammar_file = "backend/api/grammar_routes.py"
content = add_auth_import(grammar_file)

# 需要修改的端点
endpoints_to_modify = [
    'get_all_grammar_rules',
    'get_grammar_rule', 
    'create_grammar_rule',
    'update_grammar_rule',
    'delete_grammar_rule',
    'toggle_star',
    'search_grammar_rules',
    'create_grammar_example',
    'get_grammar_stats'
]

for endpoint in endpoints_to_modify:
    old_content = content
    content = add_user_param_to_endpoint(content, endpoint)
    if content != old_content:
        print(f"  ✅ {endpoint} 添加认证")

# 保存
with open(grammar_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ {grammar_file} 修改完成")

# 处理 text_routes.py
print("\n" + "="*60)
print("修改 backend/api/text_routes.py")
print("="*60)

text_file = "backend/api/text_routes.py"
content = add_auth_import(text_file)

# 需要修改的端点
text_endpoints = [
    'get_all_texts',
    'get_text',
    'create_text',
    'update_text',
    'delete_text',
    'add_sentence_to_text',
    'get_text_sentences'
]

for endpoint in text_endpoints:
    old_content = content
    content = add_user_param_to_endpoint(content, endpoint)
    if content != old_content:
        print(f"  ✅ {endpoint} 添加认证")

# 保存
with open(text_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ {text_file} 修改完成")

print("\n" + "="*60)
print("✅ 所有 API 文件已添加认证参数")
print("="*60)
print("\n⚠️  注意：还需要手动添加数据库查询的 user_id 过滤")
print("建议：参照 vocab_routes.py 的模式修改每个端点的查询逻辑")

