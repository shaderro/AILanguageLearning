from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
print("✅ SessionState singleton initialized")

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
    return {'status': 'ok'}


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
        if isinstance(item, dict) and int(item.get('grammar_id', -1)) == int(grammar_id):
            return {'data': item}
    raise HTTPException(status_code=404, detail='grammar not found')


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
    return {
        'data': {
            'vocab_count': len(vocab_data),
            'grammar_count': len(grammar_data),
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
async def chat_with_assistant(payload: dict):
    """处理用户聊天请求，调用 MainAssistant 进行问答和自动总结"""
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
        
        # 初始化 MainAssistant
        print("\n" + "-"*80)
        print("🤖 [Chat] 步骤1: 开始初始化 MainAssistant...")
        try:
            from backend.assistants.main_assistant import MainAssistant
            print("🤖 [Chat] 步骤1.1: MainAssistant 导入成功")
        except Exception as e:
            print(f"❌ [Chat] 步骤1.1失败: MainAssistant 导入失败: {e}")
            raise
        
        try:
            from backend.data_managers import data_controller
            print("🤖 [Chat] 步骤1.2: data_controller 导入成功")
        except Exception as e:
            print(f"❌ [Chat] 步骤1.2失败: data_controller 导入失败: {e}")
            raise
        
        # 使用 data_controller 实例
        print("🤖 [Chat] 步骤2: 创建 DataController 实例...")
        try:
            dc = data_controller.DataController(max_turns=100)
            print("🤖 [Chat] 步骤2完成: DataController 创建成功")
        except Exception as e:
            print(f"❌ [Chat] 步骤2失败: DataController 创建失败: {e}")
            import traceback
            print(traceback.format_exc())
            raise
        
        print("🤖 [Chat] 步骤3: 创建 MainAssistant 实例...")
        try:
            # 🔧 重要：传入同一个 session_state 实例，确保状态共享
            main_assistant = MainAssistant(
                data_controller_instance=dc,
                session_state_instance=session_state
            )
            print("🤖 [Chat] 步骤3完成: MainAssistant 创建成功")
            print("  - 使用共享的 session_state 实例")
        except Exception as e:
            print(f"❌ [Chat] 步骤3失败: MainAssistant 创建失败: {e}")
            import traceback
            print(traceback.format_exc())
            raise
        
        print("\n" + "-"*80)
        print(f"🚀 [Chat] 步骤4: 准备调用 MainAssistant.run()...")
        print(f"  - quoted_sentence: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
        print(f"  - sentence_body: {current_sentence.sentence_body[:100]}...")
        print(f"  - user_question: {current_input}")
        print(f"  - selected_text: {selected_text}")
        print("-"*80 + "\n")
        
        # 调用 MainAssistant.run()
        try:
            print("🚀 [Chat] 步骤4.1: 开始执行 main_assistant.run()...")
            main_assistant.run(
                quoted_sentence=current_sentence,
                user_question=current_input,
                selected_text=selected_text
            )
            print("🚀 [Chat] 步骤4.2: main_assistant.run() 执行完成")
        except Exception as e:
            print(f"❌ [Chat] 步骤4失败: MainAssistant.run() 执行失败: {e}")
            import traceback
            print(traceback.format_exc())
            raise
        
        # 从 session_state 获取响应
        ai_response = session_state.current_response
        print(f"✅ [Chat] AI Response: {ai_response[:100] if ai_response else 'None'}...")
        
        # 获取总结的语法和词汇
        grammar_summaries = []
        vocab_summaries = []
        
        if session_state.summarized_results:
            from backend.assistants.chat_info.session_state import GrammarSummary, VocabSummary
            for result in session_state.summarized_results:
                if isinstance(result, GrammarSummary):
                    grammar_summaries.append({
                        'name': result.grammar_rule_name,
                        'summary': result.grammar_rule_summary
                    })
                elif isinstance(result, VocabSummary):
                    vocab_summaries.append({
                        'vocab': result.vocab
                    })
        
        print(f"📚 [Chat] Summaries:")
        print(f"  - Grammar: {len(grammar_summaries)} items")
        print(f"  - Vocab: {len(vocab_summaries)} items")
        
        # 获取新增的语法和词汇
        grammar_to_add = []
        vocab_to_add = []
        
        if session_state.grammar_to_add:
            for grammar in session_state.grammar_to_add:
                grammar_to_add.append({
                    'name': grammar.rule_name,
                    'explanation': grammar.rule_explanation
                })
        
        if session_state.vocab_to_add:
            for vocab in session_state.vocab_to_add:
                vocab_to_add.append({
                    'vocab': vocab.vocab
                })
        
        print(f"🆕 [Chat] New items to add:")
        print(f"  - Grammar: {len(grammar_to_add)} items")
        print(f"  - Vocab: {len(vocab_to_add)} items")
        
        return {
            'success': True,
            'data': {
                'ai_response': ai_response,
                'grammar_summaries': grammar_summaries,
                'vocab_summaries': vocab_summaries,
                'grammar_to_add': grammar_to_add,
                'vocab_to_add': vocab_to_add
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
        
        print(f"🏷️ [AskedTokens] Marking token as asked:")
        print(f"  - user_id: {user_id}")
        print(f"  - text_id: {text_id}")
        print(f"  - sentence_id: {sentence_id}")
        print(f"  - sentence_token_id: {sentence_token_id}")
        
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
        success = manager.mark_token_asked(user_id, text_id, sentence_id, sentence_token_id)
        
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
