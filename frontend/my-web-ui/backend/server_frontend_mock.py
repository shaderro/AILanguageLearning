from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import os
import sys
import uvicorn
# Import saver with fallbacks for both package and script execution
try:
    from .server_save_to_json import save_vocab_to_json
except Exception:
    try:
        from backend.server_save_to_json import save_vocab_to_json
    except Exception:
        import importlib
        SAVE_DIR = os.path.dirname(__file__)
        if SAVE_DIR not in sys.path:
            sys.path.insert(0, SAVE_DIR)
        save_vocab_to_json = importlib.import_module('server_save_to_json').save_vocab_to_json

# Ensure project root and backend package are importable
# server.py is at: <repo>/frontend/my-web-ui/backend/server.py
# We add: <repo>/ and <repo>/backend to sys.path
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
BACKEND_DIR = os.path.join(REPO_ROOT, 'backend')
for p in [REPO_ROOT, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Import SessionState and helpers after path setup
from backend.assistants.chat_info.session_state import SessionState
from backend.assistants.chat_info.selected_token import SelectedToken
from backend.data_managers.data_classes_new import Sentence as NewSentence

print("Creating FastAPI app...")
app = FastAPI()

print("Adding CORS middleware...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Initialize global SessionState singleton
session_state = SessionState()
print("[OK] SessionState singleton initialized")

# Initialize global DataController singleton
# 路径设置
CURRENT_FILE_DIR = os.path.dirname(__file__)  # frontend/my-web-ui/backend
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_FILE_DIR, '..', '..', '..'))  # 项目根目录
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")  # backend目录
DATA_DIR = os.path.join(BACKEND_DIR, "data", "current")

GRAMMAR_PATH = os.path.join(DATA_DIR, "grammar.json")
VOCAB_PATH = os.path.join(DATA_DIR, "vocab.json")
TEXT_PATH = os.path.join(DATA_DIR, "original_texts.json")
DIALOGUE_RECORD_PATH = os.path.join(DATA_DIR, "dialogue_record.json")
DIALOGUE_HISTORY_PATH = os.path.join(DATA_DIR, "dialogue_history.json")

# 导入并初始化全局 DataController
from backend.data_managers import data_controller
global_dc = data_controller.DataController(max_turns=100)
print("✅ DataController singleton created")

# 加载数据
try:
    global_dc.load_data(
        grammar_path=GRAMMAR_PATH,
        vocab_path=VOCAB_PATH,
        text_path=TEXT_PATH,
        dialogue_record_path=DIALOGUE_RECORD_PATH,
        dialogue_history_path=DIALOGUE_HISTORY_PATH
    )
    print("✅ Global data loaded successfully")
    print(f"  - Grammar rules: {len(global_dc.grammar_manager.grammar_bundles)}")
    print(f"  - Vocab items: {len(global_dc.vocab_manager.vocab_bundles)}")
    print(f"  - Texts: {len(global_dc.text_manager.original_texts)}")
except Exception as e:
    print(f"⚠️ Global data loading failed: {e}")
    print("⚠️ Continuing with empty data")

# Build data paths relative to repository root to avoid user-dependent absolute paths
DATA_CURRENT_DIR = os.path.join(BACKEND_DIR, 'data', 'current')
vocab_file = os.path.join(DATA_CURRENT_DIR, 'vocab.json')
grammar_file = os.path.join(DATA_CURRENT_DIR, 'grammar.json')
result_dir = os.path.join(DATA_CURRENT_DIR, 'articles')
print(f"Vocab file path: {vocab_file}")
print(f"Vocab file exists: {os.path.exists(vocab_file)}")
print(f"Grammar file path: {grammar_file}")
print(f"Grammar file exists: {os.path.exists(grammar_file)}")
print(f"Result dir path: {result_dir}")
print(f"Result dir exists: {os.path.exists(result_dir)}")


# 异步保存数据的辅助函数
def save_data_async(dc, grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path):
    """
    后台异步保存数据（总是执行，确保例句更新被持久化）
    
    Args:
        dc: DataController 实例
        grammar_path: 语法数据路径
        vocab_path: 词汇数据路径
        text_path: 文本数据路径
        dialogue_record_path: 对话记录路径
        dialogue_history_path: 对话历史路径
    """
    try:
        print("\n💾 [Background] ========== 开始异步保存数据 ==========")
        dc.save_data(
            grammar_path=grammar_path,
            vocab_path=vocab_path,
            text_path=text_path,
            dialogue_record_path=dialogue_record_path,
            dialogue_history_path=dialogue_history_path
        )
        print("✅ [Background] 数据保存成功")
    except Exception as e:
        print(f"❌ [Background] 数据保存失败: {e}")
        import traceback
        print(traceback.format_exc())


def _safe_read_json(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading {path}: {e}")
    return default


def _safe_write_json(path: str, data) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error writing {path}: {e}")
        return False


@app.get('/api/debug-paths')
async def debug_paths():
    return {
        'vocab_file': vocab_file,
        'vocab_exists': os.path.exists(vocab_file),
        'grammar_file': grammar_file,
        'grammar_exists': os.path.exists(grammar_file),
        'articles_dir': result_dir,
        'articles_exists': os.path.exists(result_dir),
        'articles_files': [f for f in os.listdir(result_dir)] if os.path.exists(result_dir) else []
    }


@app.get('/api/health')
async def health():
    print("Health endpoint called")
    from datetime import datetime
    return {
        'data': {
            'status': 'ok',
            'timestamp': datetime.now().isoformat()
        }
    }


@app.get('/api/vocab-example-by-location')
async def get_vocab_example_by_location(request: Request):
    """按位置查找词汇例句"""
    try:
        # 从查询参数中获取值
        query_params = request.query_params
        text_id = int(query_params.get('text_id', 0))
        sentence_id = query_params.get('sentence_id')
        token_index = query_params.get('token_index')
        vocab_id = query_params.get('vocab_id')
        
        # 转换可选参数
        if sentence_id is not None:
            sentence_id = int(sentence_id)
        if token_index is not None:
            token_index = int(token_index)
        if vocab_id is not None:
            vocab_id = int(vocab_id)
            
        print(f"🔍 [VocabExample] Searching by location: text_id={text_id}, sentence_id={sentence_id}, token_index={token_index}, vocab_id={vocab_id}")
        
        # 使用全局 DataController 查找例句
        example = global_dc.vocab_manager.get_vocab_example_by_location(text_id, sentence_id, token_index)
        
        if example:
            if vocab_id is not None and int(example.vocab_id) != vocab_id:
                return {
                    'success': False,
                    'data': None,
                    'message': f'No vocab example found for requested vocab_id={vocab_id}'
                }
            print(f"✅ [VocabExample] Found example: {example}")
            
            # 转换为字典格式返回
            example_dict = {
                'vocab_id': example.vocab_id,
                'text_id': example.text_id,
                'sentence_id': example.sentence_id,
                'context_explanation': example.context_explanation,
                'token_indices': getattr(example, 'token_indices', [])
            }
            
            return {
                'success': True,
                'data': example_dict,
                'message': f'Found vocab example for text_id={text_id}, sentence_id={sentence_id}, token_index={token_index}'
            }
        else:
            print(f"❌ [VocabExample] No example found")
            return {
                'success': False,
                'data': None,
                'message': f'No vocab example found for text_id={text_id}, sentence_id={sentence_id}, token_index={token_index}'
            }
            
    except Exception as e:
        print(f"❌ [VocabExample] Error searching vocab example: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


@app.get('/api/vocab')
async def get_vocab_list():
    print("Vocab endpoint called")
    try:
        vocab_data = _safe_read_json(vocab_file, [])
        print(f"Loaded {len(vocab_data)} vocab items")
        return {'data': vocab_data}
    except Exception as e:
        print(f'Error loading vocab: {e}')
        return {'data': []}


@app.get('/api/vocab/{vocab_id}')
async def get_vocab_by_id(vocab_id: int):
    data = _safe_read_json(vocab_file, [])
    for item in data:
        if isinstance(item, dict) and int(item.get('vocab_id', -1)) == int(vocab_id):
            return {'data': item}
    raise HTTPException(status_code=404, detail='vocab not found')


@app.put('/api/vocab/{vocab_id}/star')
async def toggle_vocab_star(vocab_id: int, payload: dict):
    is_starred = bool(payload.get('is_starred', False))
    data = _safe_read_json(vocab_file, [])
    updated = False
    for item in data:
        if isinstance(item, dict) and int(item.get('vocab_id', -1)) == int(vocab_id):
            item['is_starred'] = is_starred
            updated = True
            break
    if not updated:
        raise HTTPException(status_code=404, detail='vocab not found')
    if not _safe_write_json(vocab_file, data):
        raise HTTPException(status_code=500, detail='failed to persist')
    return {'success': True, 'vocab_id': vocab_id, 'is_starred': is_starred}


@app.post('/api/vocab/refresh')
async def refresh_vocab_data():
    """手动刷新词汇数据"""
    print("Manual vocab refresh requested")
    try:
        vocab_data = _safe_read_json(vocab_file, [])
        print(f"Refreshed {len(vocab_data)} vocab items")
        return {'success': True, 'message': f'Successfully refreshed {len(vocab_data)} vocab items', 'data': vocab_data}
    except Exception as e:
        print(f'Error refreshing vocab: {e}')
        return {'success': False, 'message': str(e), 'data': []}


@app.get('/api/grammar')
async def get_grammar_list():
    print("Grammar endpoint called")
    data = _safe_read_json(grammar_file, [])
    print(f"Loaded {len(data)} grammar items")
    return {'data': data}


@app.get('/api/grammar/{grammar_id}')
async def get_grammar_by_id(grammar_id: int):
    data = _safe_read_json(grammar_file, [])
    for item in data:
        if isinstance(item, dict) and int(item.get('rule_id', -1)) == int(grammar_id):
            return {'data': item}
    raise HTTPException(status_code=404, detail='grammar not found')


@app.get('/api/grammar_notations/{text_id}')
async def get_grammar_notations(text_id: int):
    """获取语法注释列表"""
    # 使用绝对路径确保能找到文件
    grammar_notations_file = os.path.join(BACKEND_DIR, 'data', 'current', 'grammar_notations', 'default_user.json')
    print(f"🔍 [get_grammar_notations] Looking for file: {grammar_notations_file}")
    print(f"🔍 [get_grammar_notations] File exists: {os.path.exists(grammar_notations_file)}")
    
    data = _safe_read_json(grammar_notations_file, [])
    print(f"🔍 [get_grammar_notations] Loaded data: {len(data)} items")
    
    # 过滤出指定text_id的注释
    filtered_data = [item for item in data if item.get('text_id') == text_id]
    print(f"🔍 [get_grammar_notations] Filtered data for text_id={text_id}: {len(filtered_data)} items")
    
    return {'data': filtered_data}


@app.get('/api/grammar_notations/{text_id}/{sentence_id}')
async def get_grammar_notation_by_sentence(text_id: int, sentence_id: int):
    """获取特定句子的语法标注详情"""
    # 使用绝对路径确保能找到文件
    grammar_notations_file = os.path.join(BACKEND_DIR, 'data', 'current', 'grammar_notations', 'default_user.json')
    print(f"🔍 [get_grammar_notation_by_sentence] Looking for file: {grammar_notations_file}")
    print(f"🔍 [get_grammar_notation_by_sentence] File exists: {os.path.exists(grammar_notations_file)}")
    
    data = _safe_read_json(grammar_notations_file, [])
    print(f"🔍 [get_grammar_notation_by_sentence] Loaded data: {len(data)} items")
    
    # 查找匹配的语法标注
    matching_notation = None
    for item in data:
        if item.get('text_id') == text_id and item.get('sentence_id') == sentence_id:
            matching_notation = item
            break
    
    print(f"🔍 [get_grammar_notation_by_sentence] Found notation for {text_id}:{sentence_id}: {matching_notation is not None}")
    
    if matching_notation:
        return {'data': matching_notation}
    else:
        return {'data': None, 'message': f'No grammar notation found for text_id={text_id}, sentence_id={sentence_id}'}


@app.get('/api/vocab_notations/{text_id}')
async def get_vocab_notations(text_id: int):
    """获取词汇注释列表"""
    # 使用绝对路径确保能找到文件
    vocab_notations_file = os.path.join(BACKEND_DIR, 'data', 'current', 'vocab_notations', 'default_user.json')
    print(f"🔍 [get_vocab_notations] Looking for file: {vocab_notations_file}")
    print(f"🔍 [get_vocab_notations] File exists: {os.path.exists(vocab_notations_file)}")
    
    data = _safe_read_json(vocab_notations_file, [])
    print(f"🔍 [get_vocab_notations] Loaded data: {len(data)} items")
    
    # 过滤出指定text_id的注释
    filtered_data = [item for item in data if item.get('text_id') == text_id]
    print(f"🔍 [get_vocab_notations] Filtered data for text_id={text_id}: {len(filtered_data)} items")
    
    return {'data': filtered_data}


@app.get('/api/vocab_notations/{text_id}/{sentence_id}')
async def get_vocab_notation_by_sentence(text_id: int, sentence_id: int):
    """获取特定句子的词汇标注详情"""
    # 使用绝对路径确保能找到文件
    vocab_notations_file = os.path.join(BACKEND_DIR, 'data', 'current', 'vocab_notations', 'default_user.json')
    print(f"🔍 [get_vocab_notation_by_sentence] Looking for file: {vocab_notations_file}")
    print(f"🔍 [get_vocab_notation_by_sentence] File exists: {os.path.exists(vocab_notations_file)}")
    
    data = _safe_read_json(vocab_notations_file, [])
    print(f"🔍 [get_vocab_notation_by_sentence] Loaded data: {len(data)} items")
    
    # 查找匹配的词汇标注
    matching_notations = []
    for item in data:
        if item.get('text_id') == text_id and item.get('sentence_id') == sentence_id:
            matching_notations.append(item)
    
    print(f"🔍 [get_vocab_notation_by_sentence] Found notations for {text_id}:{sentence_id}: {len(matching_notations)} items")
    
    if matching_notations:
        return {'data': matching_notations}
    else:
        return {'data': [], 'message': f'No vocab notations found for text_id={text_id}, sentence_id={sentence_id}'}


@app.get('/api/grammar_examples/{text_id}/{sentence_id}')
async def get_grammar_examples_by_sentence(text_id: int, sentence_id: int):
    """获取指定句子的所有语法例子"""
    try:
        print(f"🔍 [get_grammar_examples_by_sentence] text_id={text_id}, sentence_id={sentence_id}")
        
        # 使用全局的DataController来获取grammar examples
        grammar_examples = []
        
        # 遍历所有语法规则，查找匹配的例句
        grammar_data = _safe_read_json(grammar_file, [])
        
        for rule in grammar_data:
            if 'examples' in rule:
                for example in rule['examples']:
                    if example.get('text_id') == text_id and example.get('sentence_id') == sentence_id:
                        grammar_examples.append({
                            'rule_id': rule.get('rule_id'),
                            'rule_name': rule.get('rule_name'),
                            'rule_summary': rule.get('rule_summary'),
                            'example': example
                        })
        
        print(f"📚 [get_grammar_examples_by_sentence] Found {len(grammar_examples)} grammar examples")
        
        return {
            'success': True,
            'data': grammar_examples,
            'text_id': text_id,
            'sentence_id': sentence_id
        }
        
    except Exception as e:
        print(f"❌ [get_grammar_examples_by_sentence] Error: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': []
        }


@app.get('/api/articles')
async def articles():
    print("Articles endpoint called")
    articles = []
    try:
        if not os.path.exists(result_dir):
            print("Articles dir not found")
            return {'data': []}
        files = os.listdir(result_dir)
        for filename in files:
            if '_processed_' in filename and filename.endswith('.json'):
                filepath = os.path.join(result_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    article = {
                        'id': data.get('text_id', 1),
                        'text_id': data.get('text_id', 1),
                        'title': data.get('text_title', 'Article'),
                        'text_title': data.get('text_title', 'Article'),
                        'summary': data.get('summary', ''),
                        'total_sentences': data.get('total_sentences', 0),
                        'total_tokens': data.get('total_tokens', 0),
                        'timestamp': filename.split('_')[-2] + '_' + filename.split('_')[-1].replace('.json', '')
                    }
                    articles.append(article)
    except Exception as e:
        print(f'Error loading articles: {e}')
    return {'data': articles}


@app.get('/api/articles/{article_id}')
async def get_article(article_id: int):
    print(f"Get article endpoint called for ID: {article_id}")
    try:
        if not os.path.exists(result_dir):
            return {'data': None}
        for filename in os.listdir(result_dir):
            if '_processed_' in filename and filename.endswith('.json'):
                filepath = os.path.join(result_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('text_id') == article_id:
                        if 'sentences' in data:
                            for sentence in data['sentences']:
                                if 'tokens' in sentence:
                                    for token in sentence['tokens']:
                                        if isinstance(token, dict) and token.get('token_type') == 'text':
                                            token['selectable'] = True
                                        else:
                                            token['selectable'] = False
                        return {'data': data}
    except Exception as e:
        print(f'Error loading article: {e}')
        return {'data': None}
    return {'data': None}


@app.get('/api/stats')
async def get_stats():
    vocab_data = _safe_read_json(vocab_file, [])
    grammar_data = _safe_read_json(grammar_file, [])
    article_count = 0
    if os.path.exists(result_dir):
        try:
            article_count = len([f for f in os.listdir(result_dir) if '_processed_' in f and f.endswith('.json')])
        except Exception:
            article_count = 0
    
    # 计算收藏的数量
    vocab_starred = sum(1 for v in vocab_data if isinstance(v, dict) and v.get('is_starred', False))
    grammar_starred = sum(1 for g in grammar_data if isinstance(g, dict) and g.get('is_starred', False))
    
    return {
        'data': {
            'vocab': {
                'total': len(vocab_data),
                'starred': vocab_starred
            },
            'grammar': {
                'total': len(grammar_data),
                'starred': grammar_starred
            },
            'article_count': article_count
        }
    }


@app.post('/api/test-token-to-vocab')
async def test_token_to_vocab(request_data: dict):
    """测试token转vocab功能"""
    print("🚀 [Backend] Test token-to-vocab endpoint called")
    print(f"📥 [Backend] Request data: {request_data}")
    
    try:
        # 解析请求数据
        token_data = request_data.get('token', {})
        
        # 优先从 session_state 获取当前句子信息，避免前端传入错误数据
        if session_state.current_sentence:
            sentence_body = session_state.current_sentence.sentence_body
            text_id = session_state.current_sentence.text_id
            sentence_id = session_state.current_sentence.sentence_id
            print(f"✅ [Backend] Using sentence from session_state:")
        else:
            # 回退到请求体传入的数据
            sentence_body = request_data.get('sentence_body', '')
            text_id = request_data.get('text_id', 1)
            sentence_id = request_data.get('sentence_id', 1)
            print(f"⚠️ [Backend] Session state empty, using request data:")
        
        print(f"🔍 [Backend] Parsed data:")
        print(f"  - Token data: {token_data}")
        print(f"  - Sentence body: {sentence_body[:50]}..." if len(sentence_body) > 50 else f"  - Sentence body: {sentence_body}")
        print(f"  - Text ID: {text_id}")
        print(f"  - Sentence ID: {sentence_id}")
        
        # 创建Token对象（使用新的数据模型）
        from backend.data_managers.data_classes_new import Token
        token = Token(
            token_body=token_data.get('token_body', ''),
            token_type=token_data.get('token_type', 'text'),
            difficulty_level=token_data.get('difficulty_level', 'hard'),
            global_token_id=token_data.get('global_token_id', 1),
            sentence_token_id=token_data.get('sentence_token_id', 1)
        )
        
        print(f"🏗️ [Backend] Created Token object:")
        print(f"  - token_body: {token.token_body}")
        print(f"  - token_type: {token.token_type}")
        print(f"  - difficulty_level: {token.difficulty_level}")
        
        # 检查词汇是否已存在（查重）
        print(f"🔍 [Backend] Checking if vocab already exists for: {token.token_body}")
        vocab_data = _safe_read_json(vocab_file, [])
        existing_vocab = None
        
        for item in vocab_data:
            if isinstance(item, dict) and item.get('vocab_body', '').lower() == token.token_body.lower():
                existing_vocab = item
                print(f"✅ [Backend] Found existing vocab! vocab_id: {item.get('vocab_id')}")
                break
        
        if existing_vocab:
            print(f"♻️ [Backend] Reusing existing vocab explanation instead of calling AI")
            
            # 设置 session state 的 current_response（复用已有解释）
            explanation = existing_vocab.get('explanation', '')
            context_explanation = existing_vocab.get('examples', [{}])[0].get('context_explanation', '') if existing_vocab.get('examples') else ''
            ai_response = explanation + ('\n\n' + context_explanation if context_explanation else '')
            
            if ai_response:
                print(f"📝 [SessionState] Setting current response (reused explanation)")
                session_state.set_current_response(ai_response)
                print("✅ [SessionState] Current response set successfully")
            
            return {'success': True, 'data': existing_vocab, 'saved_to_file': False, 'reused': True}
        
        # 词汇不存在，调用 AI 进行转换
        from backend.preprocessing.token_to_vocab import TokenToVocabConverter
        
        print("🔄 [Backend] Initializing TokenToVocabConverter...")
        converter = TokenToVocabConverter()
        
        print("⚡ [Backend] Converting token to vocab with AI...")
        vocab_result = converter.convert_token_to_vocab(token, sentence_body, text_id, sentence_id)
        
        if vocab_result:
            print("✅ [Backend] Token to vocab conversion successful!")
            print(f"📊 [Backend] Vocab result details:")
            print(f"  - vocab_id: {vocab_result.vocab_id}")
            print(f"  - vocab_body: {vocab_result.vocab_body}")
            print(f"  - explanation: {vocab_result.explanation}")
            print(f"  - source: {vocab_result.source}")
            print(f"  - examples count: {len(vocab_result.examples)}")
            
            # 转换为字典格式返回
            vocab_dict = {
                'vocab_id': vocab_result.vocab_id,
                'vocab_body': vocab_result.vocab_body,
                'explanation': vocab_result.explanation,
                'source': vocab_result.source,
                'is_starred': vocab_result.is_starred,
                'examples': [
                    {
                        'vocab_id': ex.vocab_id,
                        'text_id': ex.text_id,
                        'sentence_id': ex.sentence_id,
                        'context_explanation': ex.context_explanation,
                        'token_indices': ex.token_indices
                    } for ex in vocab_result.examples
                ]
            }
            
            # 🆕 保存到 vocab.json 文件（模块化）
            print("💾 [Backend] Attempting to save vocab to JSON file...")
            try:
                final_id, total_count = save_vocab_to_json(vocab_file, vocab_dict)
                vocab_dict['vocab_id'] = final_id
                print(f"✅ [Backend] Successfully saved vocab to file! vocab_id: {final_id}")
                print(f"📈 [Backend] Total vocab count: {total_count}")
            except Exception as save_error:
                print(f"⚠️ [Backend] Failed to save to file: {save_error}")
                print("🔄 [Backend] Continuing with response anyway...")
            
            print(f"🎉 [Backend] Final vocab dict: {json.dumps(vocab_dict, ensure_ascii=False, indent=2)}")
            
            # 设置 session state 的 current_response
            explanation = vocab_dict.get('explanation', '')
            context_explanation = vocab_dict.get('examples', [{}])[0].get('context_explanation', '') if vocab_dict.get('examples') else ''
            ai_response = explanation + ('\n\n' + context_explanation if context_explanation else '')
            
            if ai_response:
                print(f"📝 [SessionState] Setting current response (AI explanation)")
                session_state.set_current_response(ai_response)
                print("✅ [SessionState] Current response set successfully")
            
            return {'success': True, 'data': vocab_dict, 'saved_to_file': True}
        else:
            print("❌ [Backend] Failed to convert token to vocab")
            return {'success': False, 'error': 'Failed to convert token to vocab'}
    except Exception as e:
        # 将后端详细错误透传给前端，便于调试
        print(f'💥 [Backend] Error in test-token-to-vocab: {e}')
        import traceback
        tb = traceback.format_exc()
        print(f'🔍 [Backend] Full traceback:\n{tb}')
        return {
            'success': False,
            'error': str(e),
            'traceback': tb,
        }


@app.post('/api/session/set_sentence')
async def set_session_sentence(payload: dict):
    """设置当前会话的句子上下文"""
    try:
        text_id = payload.get('text_id')
        sentence_id = payload.get('sentence_id')
        sentence_body = payload.get('sentence_body', '')
        
        # 检查是否需要更新
        current_sentence = session_state.current_sentence
        needs_update = False
        
        if current_sentence is None:
            needs_update = True
            print(f"📝 [SessionState] Current sentence is empty, setting new sentence")
        elif current_sentence.text_id != text_id or current_sentence.sentence_id != sentence_id:
            needs_update = True
            print(f"🔄 [SessionState] Sentence changed (was: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id})")
        else:
            print(f"✓ [SessionState] Current sentence unchanged, skipping update")
        
        if needs_update:
            print(f"📝 [SessionState] Setting current sentence:")
            print(f"  - text_id: {text_id}")
            print(f"  - sentence_id: {sentence_id}")
            print(f"  - sentence_body: {sentence_body[:50]}..." if len(sentence_body) > 50 else f"  - sentence_body: {sentence_body}")
            
            # 构造 Sentence 对象
            sentence = NewSentence(
                text_id=text_id,
                sentence_id=sentence_id,
                sentence_body=sentence_body,
                grammar_annotations=[],
                vocab_annotations=[],
                tokens=[]
            )
            
            session_state.set_current_sentence(sentence)
            print("✅ [SessionState] Current sentence set successfully")
        
        return {
            'success': True,
            'message': 'Sentence context updated' if needs_update else 'Sentence context unchanged',
            'updated': needs_update,
            'sentence_info': {
                'text_id': text_id,
                'sentence_id': sentence_id,
                'sentence_body': sentence_body
            }
        }
    except Exception as e:
        print(f"❌ [SessionState] Error setting sentence: {e}")
        return {'success': False, 'error': str(e)}


@app.post('/api/session/select_token')
async def set_session_selected_token(payload: dict):
    """设置当前会话选中的 token"""
    try:
        token_data = payload.get('token', {})
        
        print(f"🎯 [SessionState] Setting selected token:")
        print(f"  - token_body: {token_data.get('token_body')}")
        print(f"  - global_token_id: {token_data.get('global_token_id')}")
        print(f"  - sentence_token_id: {token_data.get('sentence_token_id')}")
        
        # 从当前 session_state 获取句子信息
        current_sentence = session_state.current_sentence
        if not current_sentence:
            return {'success': False, 'error': 'No sentence context available. Please set sentence first.'}
        
        # 构造 SelectedToken 对象
        # 如果有 sentence_token_id，用它作为索引；否则表示整句选择
        token_indices = []
        if token_data.get('sentence_token_id') is not None:
            token_indices = [token_data.get('sentence_token_id')]
        else:
            # 没有 token_id，表示选择整句话
            token_indices = [-1]
        
        # 检查是否为空列表（防止错误）
        if not token_indices:
            token_indices = [-1]  # 默认为整句选择
        
        selected_token = SelectedToken(
            token_indices=token_indices,
            token_text=token_data.get('token_body', current_sentence.sentence_body),
            sentence_body=current_sentence.sentence_body,
            sentence_id=current_sentence.sentence_id,
            text_id=current_sentence.text_id
        )
        
        session_state.set_current_selected_token(selected_token)
        print("✅ [SessionState] Selected token set successfully")
        print(f"  - Token indices: {token_indices}")
        print(f"  - Is full sentence: {token_indices == [-1]}")
        
        return {
            'success': True,
            'message': 'Selected token updated',
            'token_info': {
                'token_text': token_data.get('token_body'),
                'token_indices': token_indices
            }
        }
    except Exception as e:
        import traceback
        print(f"❌ [SessionState] Error setting selected token: {e}")
        print(f"🔍 [SessionState] Traceback:\n{traceback.format_exc()}")
        return {'success': False, 'error': str(e)}


@app.post('/api/session/update_context')
async def update_session_context(payload: dict):
    """一次性更新会话上下文（批量更新）"""
    try:
        print(f"🔄 [SessionState] Updating session context (batch):")
        print(f"  - Payload: {payload}")
        
        updated_fields = []
        
        # 更新 current_input
        if 'current_input' in payload:
            current_input = payload['current_input']
            session_state.set_current_input(current_input)
            updated_fields.append('current_input')
            print(f"  ✓ current_input set: {current_input[:50]}..." if len(current_input) > 50 else f"  ✓ current_input set: {current_input}")
        
        # 更新句子信息（如果提供）
        if 'sentence' in payload:
            sentence_data = payload['sentence']
            text_id = sentence_data.get('text_id', 0)
            sentence_id = sentence_data.get('sentence_id', 0)
            sentence_body = sentence_data.get('sentence_body', '')
            
            sentence = NewSentence(
                text_id=text_id,
                sentence_id=sentence_id,
                sentence_body=sentence_body,
                grammar_annotations=[],
                vocab_annotations=[],
                tokens=[]
            )
            session_state.set_current_sentence(sentence)
            updated_fields.append('sentence')
            print(f"  ✓ sentence set: text_id={text_id}, sentence_id={sentence_id}")
        
        # 更新选中的 token（如果提供）
        # 注意：如果 payload 中显式包含 'token' 字段（即使值为 None），也会进入这个分支
        if 'token' in payload:
            token_data = payload.get('token')
            
            # 如果 token_data 为 None 或空，清除 token 选择（表示整句话提问）
            if token_data is None or (isinstance(token_data, dict) and not token_data):
                print(f"  ✓ token cleared (整句话提问)")
                current_sentence = session_state.current_sentence
                if current_sentence:
                    # 创建一个表示整句话的 SelectedToken
                    selected_token = SelectedToken(
                        token_indices=[-1],
                        token_text=current_sentence.sentence_body,
                        sentence_body=current_sentence.sentence_body,
                        sentence_id=current_sentence.sentence_id,
                        text_id=current_sentence.text_id
                    )
                    session_state.set_current_selected_token(selected_token)
                    updated_fields.append('token')
            else:
                # 有具体的 token 数据
                current_sentence = session_state.current_sentence
                
                if current_sentence:
                    # 检查是否是多选token的情况
                    if token_data.get('multiple_tokens') is not None:
                        # 多选token的情况
                        multiple_tokens = token_data.get('multiple_tokens', [])
                        token_indices = token_data.get('token_indices', [])
                        token_text = token_data.get('token_text', '')
                        
                        print(f"  ✓ multiple tokens detected: {len(multiple_tokens)} tokens")
                        print(f"  ✓ token indices: {token_indices}")
                        print(f"  ✓ combined text: {token_text}")
                        
                        selected_token = SelectedToken(
                            token_indices=token_indices,
                            token_text=token_text,
                            sentence_body=current_sentence.sentence_body,
                            sentence_id=current_sentence.sentence_id,
                            text_id=current_sentence.text_id
                        )
                        session_state.set_current_selected_token(selected_token)
                        updated_fields.append('token')
                        print(f"  ✓ multiple tokens set: {token_text} (indices: {token_indices})")
                    else:
                        # 单选token的情况（原有逻辑）
                        token_indices = []
                        if token_data.get('sentence_token_id') is not None:
                            token_indices = [token_data.get('sentence_token_id')]
                        else:
                            # 没有 token_id，表示选择整句话
                            token_indices = [-1]
                        
                        # 检查是否为空列表（防止错误）
                        if not token_indices:
                            token_indices = [-1]  # 默认为整句选择
                        
                        selected_token = SelectedToken(
                            token_indices=token_indices,
                            token_text=token_data.get('token_body', current_sentence.sentence_body),
                            sentence_body=current_sentence.sentence_body,
                            sentence_id=current_sentence.sentence_id,
                            text_id=current_sentence.text_id
                        )
                        session_state.set_current_selected_token(selected_token)
                        updated_fields.append('token')
                        print(f"  ✓ single token set: {token_data.get('token_body')} (indices: {token_indices})")
        
        print(f"✅ [SessionState] Context updated: {', '.join(updated_fields)}")
        return {
            'success': True,
            'message': 'Session context updated',
            'updated_fields': updated_fields
        }
    except Exception as e:
        import traceback
        print(f"❌ [SessionState] Error updating context: {e}")
        print(f"🔍 [SessionState] Traceback:\n{traceback.format_exc()}")
        return {'success': False, 'error': str(e)}


@app.post('/api/chat')
async def chat_with_assistant(payload: dict, background_tasks: BackgroundTasks):
    """处理用户聊天请求：立即返回主回答，其余流程在后台异步执行"""
    try:
        print("\n" + "="*80)
        print("💬 [Chat] ========== Chat endpoint called ==========")
        print(f"📥 [Chat] Payload: {payload}")
        print("="*80)
        
        # 从 session_state 获取上下文信息
        current_sentence = session_state.current_sentence
        current_selected_token = session_state.current_selected_token
        current_input = session_state.current_input
        
        print(f"📋 [Chat] Session State Info:")
        print(f"  - current_input: {current_input}")
        print(f"  - current_sentence: {current_sentence.sentence_body[:50] if current_sentence else 'None'}...")
        print(f"  - current_selected_token: {current_selected_token.token_text if current_selected_token else 'None'}")
        
        # 验证必要的参数
        if not current_sentence:
            print("⚠️ [Chat] No sentence in session_state, this is a problem!")
            return {
                'success': False,
                'error': 'No sentence context in session state. Please select a sentence first.'
            }
        
        if not current_input:
            # 如果 session_state 中没有 current_input，尝试从 payload 获取
            current_input = payload.get('user_question', '')
            if not current_input:
                print("⚠️ [Chat] No user question provided!")
                return {
                    'success': False,
                    'error': 'No user question provided'
                }
            session_state.set_current_input(current_input)
            print(f"📝 [Chat] Set current_input from payload: {current_input}")
        
        # 准备 selected_text（如果用户选择了特定 token）
        selected_text = None
        
        print(f"🔍 [Chat] Analyzing selected_token:")
        print(f"  - current_selected_token: {current_selected_token}")
        if current_selected_token:
            print(f"  - token_text: '{current_selected_token.token_text}'")
            print(f"  - token_indices: {getattr(current_selected_token, 'token_indices', 'N/A')}")
        
        if current_selected_token and current_selected_token.token_text:
            # 检查是否是整句选择（token_indices 为 [-1]）
            if hasattr(current_selected_token, 'token_indices') and current_selected_token.token_indices == [-1]:
                # 整句选择，不设置 selected_text
                selected_text = None
                print(f"📖 [Chat] User is asking about the full sentence (from session token with indices=[-1])")
            elif current_selected_token.token_text.strip() == current_sentence.sentence_body.strip():
                # 选择的文本就是整句话
                selected_text = None
                print(f"📖 [Chat] User is asking about the full sentence (text matches sentence)")
            else:
                # 选择了特定 token
                selected_text = current_selected_token.token_text
                print(f"🎯 [Chat] User selected specific token: '{selected_text}'")
        else:
            print(f"📖 [Chat] User is asking about the full sentence (no token selected)")
        
        # 使用全局 DataController（复用实例，保持数据持久性）
        print("\n" + "-"*80)
        print("🤖 [Chat] 步骤1: 使用全局 DataController 实例...")
        try:
            from backend.assistants.main_assistant import MainAssistant
            print("🤖 [Chat] 步骤1.1: MainAssistant 导入成功")
        except Exception as e:
            print(f"❌ [Chat] 步骤1.1失败: MainAssistant 导入失败: {e}")
            raise
        
        # 使用全局 DataController 实例（不再每次创建新实例）
        dc = global_dc
        print(f"🤖 [Chat] 步骤2: 使用全局 DataController")
        print(f"  - Grammar rules: {len(dc.grammar_manager.grammar_bundles)}")
        print(f"  - Vocab items: {len(dc.vocab_manager.vocab_bundles)}")
        print(f"  - Texts: {len(dc.text_manager.original_texts)}")
        
        print("🤖 [Chat] 步骤3: 创建 MainAssistant 实例...")
        try:
            # 🔧 重要：传入全局 dc 和 session_state 实例，确保状态共享
            main_assistant = MainAssistant(
                data_controller_instance=dc,
                session_state_instance=session_state
            )
            print("🤖 [Chat] 步骤3完成: MainAssistant 创建成功")
            print("  - 使用共享的 dc 和 session_state 实例")
        except Exception as e:
            print(f"❌ [Chat] 步骤3失败: MainAssistant 创建失败: {e}")
            import traceback
            print(traceback.format_exc())
            raise
        
        print("\n" + "-"*80)
        print(f"🚀 [Chat] 步骤4: 完整流程...")
        print(f"  - quoted_sentence: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
        print(f"  - sentence_body: {current_sentence.sentence_body[:100]}...")
        print(f"  - user_question: {current_input}")
        print(f"  - selected_text: {selected_text}")
        print("-"*80 + "\n")

        # —— 先返回主回答，其余完整流程放后台 ——
        try:
            effective_sentence_body = selected_text if selected_text else current_sentence.sentence_body
            print("🚀 [Chat] 调用 answer_question_function() 生成主回答（将立即返回）...")
            ai_response = main_assistant.answer_question_function(
                quoted_sentence=current_sentence,
                user_question=current_input,
                sentence_body=effective_sentence_body
            )
            print("✅ [Chat] 主回答就绪，将立即返回给前端（不再等待后续流程）")
        except Exception as e:
            print(f"❌ [Chat] 生成主回答失败: {e}")
            import traceback
            print(traceback.format_exc())
            raise

        # 同步执行：轻量级语法/词汇总结，用于前端即时展示（不做持久化）
        grammar_summaries = []
        vocab_summaries = []
        grammar_to_add = []
        vocab_to_add = []
        # 预先记录本轮之前已有的 vocab notations（用于后续差集推断）
        notation_manager = None
        initial_vocab_keys = set()
        user_id_for_notation = getattr(session_state, 'user_id', None) or payload.get('user_id') or 'default_user'
        try:
            from backend.data_managers.unified_notation_manager import get_unified_notation_manager
            notation_manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
            if current_sentence and hasattr(current_sentence, 'text_id'):
                initial_vocab_keys = notation_manager.get_notations(
                    notation_type="vocab",
                    text_id=current_sentence.text_id,
                    user_id=user_id_for_notation
                ) or set()
                if not isinstance(initial_vocab_keys, set):
                    initial_vocab_keys = set(initial_vocab_keys)
        except Exception as pre_e:
            print(f"⚠️ [Chat] 预读取 vocab notations 失败（忽略）: {pre_e}")

        try:
            from backend.assistants import main_assistant as _ma_mod
            prev_disable_grammar = getattr(_ma_mod, 'DISABLE_GRAMMAR_FEATURES', True)
            _ma_mod.DISABLE_GRAMMAR_FEATURES = False
            print("🧠 [Chat] 同步执行 handle_grammar_vocab_function 以便前端即时展示...")
            main_assistant.handle_grammar_vocab_function(
                quoted_sentence=current_sentence,
                user_question=current_input,
                ai_response=ai_response,
                effective_sentence_body=effective_sentence_body
            )
            
            # 🔧 关键修复：调用 add_new_to_data() 以创建新词汇和 notations
            print("🧠 [Chat] 同步执行 add_new_to_data() 以创建词汇和 notations...")
            main_assistant.add_new_to_data()
            print("✅ [Chat] add_new_to_data() 完成")
            
            # 组装摘要
            if session_state.summarized_results:
                from backend.assistants.chat_info.session_state import GrammarSummary, VocabSummary
                for result in session_state.summarized_results:
                    if isinstance(result, GrammarSummary):
                        grammar_summaries.append({'name': result.grammar_rule_name, 'summary': result.grammar_rule_summary})
                    elif isinstance(result, VocabSummary):
                        vocab_summaries.append({'vocab': result.vocab})
            if session_state.grammar_to_add:
                for g in session_state.grammar_to_add:
                    grammar_to_add.append({'name': g.rule_name, 'explanation': g.rule_explanation})
            if session_state.vocab_to_add:
                # 🔧 关键修复：从数据库查询新创建的词汇，确保 vocab_id 正确
                print(f"🔍 [Chat] 处理 session_state.vocab_to_add: {len(session_state.vocab_to_add)} 个词汇")
                for v in session_state.vocab_to_add:
                    vocab_body = getattr(v, 'vocab', None)
                    vocab_id = None
                    
                    # 首先尝试从数据库查询（因为 add_new_to_data() 刚刚创建了这些词汇）
                    try:
                        from database_system.database_manager import DatabaseManager
                        from database_system.business_logic.models import VocabExpression
                        db_manager = DatabaseManager('development')
                        session = db_manager.get_session()
                        try:
                            vocab_model = session.query(VocabExpression).filter(
                                VocabExpression.vocab_body == vocab_body,
                                VocabExpression.user_id == user_id_for_notation
                            ).order_by(VocabExpression.vocab_id.desc()).first()
                            if vocab_model:
                                vocab_id = vocab_model.vocab_id
                                print(f"✅ [Chat] 从数据库找到 vocab_id={vocab_id} for vocab='{vocab_body}'")
                        finally:
                            session.close()
                    except Exception as db_err:
                        print(f"⚠️ [Chat] 从数据库查询 vocab_id 失败: {db_err}")
                    
                    # 如果数据库查询失败，回退到从全局词库查找
                    if vocab_id is None:
                        for vid, vbundle in global_dc.vocab_manager.vocab_bundles.items():
                            vocab_body_from_bundle = getattr(vbundle, 'vocab_body', None) or (getattr(vbundle, 'vocab', None) and getattr(vbundle.vocab, 'vocab_body', None))
                            if vocab_body_from_bundle == vocab_body:
                                vocab_id = vid
                                print(f"✅ [Chat] 从全局词库找到 vocab_id={vocab_id} for vocab='{vocab_body}'")
                                break
                    
                    if vocab_id:
                        vocab_to_add.append({'vocab': vocab_body, 'vocab_id': vocab_id})
                        print(f"✅ [Chat] 添加 vocab_to_add: vocab='{vocab_body}', vocab_id={vocab_id}")
                    else:
                        print(f"⚠️ [Chat] 无法找到 vocab_id for vocab='{vocab_body}'，但仍添加到响应中")
                        vocab_to_add.append({'vocab': vocab_body, 'vocab_id': None})
            print("✅ [Chat] 即时摘要准备完成：", {
                'grammar_summaries': len(grammar_summaries),
                'vocab_summaries': len(vocab_summaries),
                'grammar_to_add': len(grammar_to_add),
                'vocab_to_add': len(vocab_to_add)
            })
        except Exception as lite_e:
            print(f"⚠️ [Chat] 同步摘要生成失败，忽略（不影响主回答）: {lite_e}")
        finally:
            try:
                _ma_mod.DISABLE_GRAMMAR_FEATURES = prev_disable_grammar
            except Exception:
                pass

        # 🔧 关键修复：在启动后台任务前，先保存当前的 created_notations
        # 因为后台任务会调用 reset_processing_results() 清空这些数据
        created_grammar_notations_snapshot = list(session_state.created_grammar_notations) if hasattr(session_state, 'created_grammar_notations') else []
        created_vocab_notations_snapshot = list(session_state.created_vocab_notations) if hasattr(session_state, 'created_vocab_notations') else []

        # 🔧 差集推断：如果 snapshot 为空，尝试用本次新增的 vocab notations 推断
        try:
            if notation_manager and current_sentence and hasattr(current_sentence, 'text_id'):
                latest_vocab_keys = notation_manager.get_notations(
                    notation_type="vocab",
                    text_id=current_sentence.text_id,
                    user_id=user_id_for_notation
                ) or set()
                if not isinstance(latest_vocab_keys, set):
                    latest_vocab_keys = set(latest_vocab_keys)
                new_keys = latest_vocab_keys - initial_vocab_keys
                if new_keys:
                    inferred = []
                    for key in new_keys:
                        # 解析 key: text_id:sentence_id:token_id
                        parts = str(key).split(':')
                        if len(parts) != 3:
                            continue
                        try:
                            _, s_id, t_id = parts
                            sentence_id = int(s_id)
                            token_id = int(t_id)
                        except Exception:
                            continue
                        try:
                            detail = notation_manager.get_notation_details(
                                notation_type="vocab",
                                user_id=user_id_for_notation,
                                text_id=current_sentence.text_id,
                                sentence_id=sentence_id,
                                token_id=token_id
                            )
                        except Exception as det_e:
                            print(f"⚠️ [Chat] 获取 notation 详情失败: {det_e}")
                            detail = None
                        vocab_id = None
                        if detail is not None and hasattr(detail, 'vocab_id'):
                            vocab_id = detail.vocab_id
                        vocab_name = None
                        if vocab_id and vocab_id in dc.vocab_manager.vocab_bundles:
                            vb = dc.vocab_manager.vocab_bundles[vocab_id]
                            vocab_name = getattr(vb, 'vocab_body', None) or getattr(getattr(vb, 'vocab', None), 'vocab_body', None)
                        inferred.append({
                            'text_id': current_sentence.text_id,
                            'sentence_id': sentence_id,
                            'token_id': token_id,
                            'vocab_id': vocab_id,
                            'vocab': vocab_name,
                            'user_id': user_id_for_notation
                        })
                    if inferred and not created_vocab_notations_snapshot:
                        created_vocab_notations_snapshot = inferred
        except Exception as diff_e:
            print(f"⚠️ [Chat] 差集推断 created_vocab_notations 失败: {diff_e}")
        
        # 🔧 Fallback: 如果 vocab_to_add 为空，但有新建的 vocab notation，尝试根据 vocab_id 补全 vocab 名称
        if (not vocab_to_add) and created_vocab_notations_snapshot:
            try:
                vocab_names = []
                for n in created_vocab_notations_snapshot:
                    vid = n.get('vocab_id')
                    if vid and vid in global_dc.vocab_manager.vocab_bundles:
                        vb = global_dc.vocab_manager.vocab_bundles[vid]
                        # 新结构或旧结构下的 vocab 字段名称
                        vocab_body = getattr(vb, 'vocab_body', None) or getattr(vb.vocab, 'vocab_body', None)
                        if vocab_body:
                            vocab_names.append({'vocab': vocab_body, 'vocab_id': vid})
                            # 也把名称写回 snapshot，方便前端直接使用
                            n['vocab'] = vocab_body
                # 去重后再写入
                if vocab_names:
                    seen = set()
                    dedup = []
                    for v in vocab_names:
                        key = v['vocab_id']
                        if key in seen:
                            continue
                        seen.add(key)
                        dedup.append(v)
                    vocab_to_add = dedup
            except Exception as enrich_err:
                print(f"⚠️ [Chat] Fallback enrich vocab_to_add failed: {enrich_err}")
        
        print(f"📸 [Chat] 快照 notations（启动后台任务前）:")
        print(f"  - Grammar notations: {len(created_grammar_notations_snapshot)}")
        print(f"  - Vocab notations: {len(created_vocab_notations_snapshot)}")

        # 后台执行持久化流程（不再重新调用 main_assistant.run，只做数据保存）
        # 因为同步流程已经完成了所有必要的处理（回答、摘要、notation创建）
        def _run_persistence_background():
            try:
                print("\n💾 [Background] 启动数据持久化任务...")
                save_data_async(
                    dc=dc,
                    grammar_path=GRAMMAR_PATH,
                    vocab_path=VOCAB_PATH,
                    text_path=TEXT_PATH,
                    dialogue_record_path=DIALOGUE_RECORD_PATH,
                    dialogue_history_path=DIALOGUE_HISTORY_PATH
                )
                print("✅ [Background] 数据持久化完成")
            except Exception as bg_e:
                print(f"❌ [Background] 持久化失败: {bg_e}")
                import traceback
                print(traceback.format_exc())

        background_tasks.add_task(_run_persistence_background)

        # 立即返回主回答和即时摘要（用于前端直接更新UI）
        # 🔧 使用快照而不是直接读取 session_state（避免被后台任务清空）
        print(f"📋 [Chat] 返回给前端的 notations（快照）:")
        print(f"  - Grammar notations: {len(created_grammar_notations_snapshot)}")
        print(f"  - Vocab notations: {len(created_vocab_notations_snapshot)}")
        if created_grammar_notations_snapshot:
            print(f"  - Grammar notation details: {created_grammar_notations_snapshot}")
        
        return {
            'success': True,
            'data': {
                'ai_response': ai_response,
                'grammar_summaries': grammar_summaries,
                'vocab_summaries': vocab_summaries,
                'grammar_to_add': grammar_to_add,
                'vocab_to_add': vocab_to_add,
                'created_grammar_notations': created_grammar_notations_snapshot,
                'created_vocab_notations': created_vocab_notations_snapshot
            }
        }
        
    except Exception as e:
        import traceback
        print("\n" + "!"*80)
        print(f"❌❌❌ [Chat] 发生严重错误 ❌❌❌")
        print(f"❌ [Chat] 错误类型: {type(e).__name__}")
        print(f"❌ [Chat] 错误消息: {e}")
        print(f"❌ [Chat] 错误详细堆栈:")
        print(traceback.format_exc())
        print("!"*80 + "\n")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }


@app.get('/api/user/asked-tokens')
async def get_asked_tokens(user_id: str = 'default_user', text_id: int = 1):
    """获取用户已提问的token列表"""
    try:
        print(f"🔍 [AskedTokens] Getting asked tokens for user_id={user_id}, text_id={text_id}")
        
        # 导入AskedTokensManager
        from backend.data_managers.asked_tokens_manager import get_asked_tokens_manager
        
        # 获取管理器实例
        manager = get_asked_tokens_manager(use_database=False)
        
        # 获取已提问的token
        asked_tokens = manager.get_asked_tokens_for_article(user_id, text_id)
        
        print(f"✅ [AskedTokens] Found {len(asked_tokens)} asked tokens")
        print(f"📋 [AskedTokens] Asked tokens: {list(asked_tokens)}")
        
        return {
            'success': True,
            'data': {
                'asked_tokens': list(asked_tokens)
            }
        }
    except Exception as e:
        print(f"❌ [AskedTokens] Error getting asked tokens: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'data': {
                'asked_tokens': []
            }
        }


@app.post('/api/user/asked-tokens')
async def mark_token_asked(payload: dict):
    """标记token为已提问"""
    try:
        user_id = payload.get('user_id', 'default_user')
        text_id = payload.get('text_id')
        sentence_id = payload.get('sentence_id')
        sentence_token_id = payload.get('sentence_token_id')
        vocab_id = payload.get('vocab_id')
        grammar_id = payload.get('grammar_id')
        
        print(f"🏷️ [AskedTokens] Marking token as asked:")
        print(f"  - user_id: {user_id}")
        print(f"  - text_id: {text_id}")
        print(f"  - sentence_id: {sentence_id}")
        print(f"  - sentence_token_id: {sentence_token_id}")
        print(f"  - vocab_id: {vocab_id}")
        print(f"  - grammar_id: {grammar_id}")
        
        if text_id is None or sentence_id is None or sentence_token_id is None:
            return {
                'success': False,
                'error': 'Missing required parameters: text_id, sentence_id, sentence_token_id'
            }
        
        # 导入AskedTokensManager
        from backend.data_managers.asked_tokens_manager import get_asked_tokens_manager
        
        # 获取管理器实例
        manager = get_asked_tokens_manager(use_database=False)
        
        # 标记token为已提问
        success = manager.mark_token_asked(user_id, text_id, sentence_id, sentence_token_id, vocab_id, grammar_id)
        
        if success:
            print(f"✅ [AskedTokens] Token marked as asked successfully")
            return {
                'success': True,
                'message': 'Token marked as asked'
            }
        else:
            print(f"❌ [AskedTokens] Failed to mark token as asked")
            return {
                'success': False,
                'error': 'Failed to mark token as asked'
            }
    except Exception as e:
        print(f"❌ [AskedTokens] Error marking token as asked: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@app.post('/api/session/reset')
async def reset_session():
    """重置会话状态"""
    try:
        print("🔄 [SessionState] Resetting session state...")
        session_state.reset()
        print("✅ [SessionState] Session state reset successfully")
        return {'success': True, 'message': 'Session state reset'}
    except Exception as e:
        print(f"❌ [SessionState] Error resetting session: {e}")
        return {'success': False, 'error': str(e)}



if __name__ == '__main__':
    print('Starting debug API server on port 8000...')
    uvicorn.run(app, host='0.0.0.0', port=8000)
