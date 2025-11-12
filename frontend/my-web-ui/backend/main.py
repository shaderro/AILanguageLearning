from fastapi import FastAPI, Query, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import requests
import uuid
from datetime import datetime

# 首先设置路径
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
BACKEND_DIR = os.path.join(REPO_ROOT, 'backend')

# 添加路径到 sys.path
for p in [REPO_ROOT, BACKEND_DIR, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# 切换工作目录到项目根目录，确保数据库路径正确
original_cwd = os.getcwd()
os.chdir(REPO_ROOT)
print(f"[OK] 工作目录已切换: {original_cwd} -> {REPO_ROOT}")

# 导入自定义模块（现在使用绝对路径导入）
sys.path.insert(0, CURRENT_DIR)
from models import ApiResponse
from services import data_service
from utils import create_success_response, create_error_response

# 导入预处理模块
try:
    from backend.preprocessing.article_processor import process_article, save_structured_data
    print("[OK] 使用简单文章处理器 (无AI依赖)")
except ImportError as e:
    print(f"Warning: Could not import article_processor: {e}")
    process_article = None
    save_structured_data = None

# 导入 asked tokens manager
from backend.data_managers.asked_tokens_manager import get_asked_tokens_manager

# 导入新的标注API路由
try:
    from backend.api.notation_routes import router as notation_router
    print("[OK] 加载新的标注API路由")
except ImportError as e:
    print(f"Warning: Could not import notation_routes: {e}")
    notation_router = None

# 计算 backend/data/current/articles 目录（相对本文件位置）
RESULT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "data", "current", "articles")
)

def _ensure_result_dir() -> str:
    os.makedirs(RESULT_DIR, exist_ok=True)
    return RESULT_DIR

def _parse_timestamp_from_filename(name: str) -> str:
    # 形如: hp1_processed_20250916_123831.json
    try:
        ts = name.rsplit("_", 2)[-2:]  # [YYYYMMDD, HHMMSS.json]
        ts_s = ts[0] + "_" + ts[1].replace(".json", "")
        # 返回 ISO-ish 格式
        dt = datetime.strptime(ts_s, "%Y%m%d_%H%M%S")
        return dt.isoformat()
    except Exception:
        return ""

def _iter_processed_files():
    base = _ensure_result_dir()
    try:
        for fname in os.listdir(base):
            if fname.endswith(".json") and "_processed_" in fname:
                yield os.path.join(base, fname)
    except FileNotFoundError:
        return

def _iter_article_dirs():
    """扫描形如 text_<id> 的目录。"""
    base = _ensure_result_dir()
    try:
        for fname in os.listdir(base):
            full_path = os.path.join(base, fname)
            if os.path.isdir(full_path) and fname.startswith("text_"):
                yield full_path
    except FileNotFoundError:
        return

def _load_article_summary_from_dir(dir_path: str):
    """从 text_<id> 目录组装文章摘要信息。"""
    try:
        # original_text.json 提供 text_id 与 text_title
        original_path = os.path.join(dir_path, "original_text.json")
        sentences_path = os.path.join(dir_path, "sentences.json")
        tokens_path = os.path.join(dir_path, "tokens.json")

        if not os.path.exists(original_path):
            return None

        original = _load_json_file(original_path)
        text_id = int(original.get("text_id", 0))
        title = original.get("text_title", "")

        total_sentences = 0
        if os.path.exists(sentences_path):
            try:
                s = _load_json_file(sentences_path)
                total_sentences = len(s) if isinstance(s, list) else 0
            except Exception:
                total_sentences = 0

        total_tokens = 0
        if os.path.exists(tokens_path):
            try:
                t = _load_json_file(tokens_path)
                total_tokens = len(t) if isinstance(t, list) else 0
            except Exception:
                total_tokens = 0

        return {
            "text_id": text_id,
            "text_title": title,
            "total_sentences": total_sentences,
            "total_tokens": total_tokens,
            # 使用目录名作为时间信息占位；也可将创建时间作为 created_at
            "created_at": None,
            "dir": os.path.basename(dir_path),
        }
    except Exception as e:
        print(f"Error summarizing dir {dir_path}: {e}")
        return None

def _load_json_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _collect_articles_summary():
    """同时兼容历史 *_processed_*.json 文件与新结构 text_<id>/ 目录。"""
    summaries = []

    # 1) 兼容历史单文件结构
    for path in _iter_processed_files():
        try:
            data = _load_json_file(path)
            text_id = int(data.get("text_id", 0))
            title = data.get("text_title", "")
            total_sentences = data.get("total_sentences", 0)
            total_tokens = data.get("total_tokens", 0)

            filename = os.path.basename(path)
            timestamp = _parse_timestamp_from_filename(filename)

            summaries.append({
                "text_id": text_id,
                "text_title": title,
                "total_sentences": total_sentences,
                "total_tokens": total_tokens,
                "created_at": timestamp,
                "filename": filename,
            })
        except Exception as e:
            print(f"Error processing {path}: {e}")
            continue

    # 2) 新目录结构
    for d in _iter_article_dirs():
        summary = _load_article_summary_from_dir(d)
        if summary is not None:
            summaries.append(summary)

    return summaries

def _find_article_dir_by_id(article_id: int):
    """根据文章ID查找对应的 text_<id> 目录。"""
    target_dir_name = f"text_{article_id}"
    for d in _iter_article_dirs():
        if os.path.basename(d) == target_dir_name:
            return d
        # 兜底：读取 original_text.json 校验 id
        try:
            original_path = os.path.join(d, "original_text.json")
            if os.path.exists(original_path):
                data = _load_json_file(original_path)
                if int(data.get("text_id", -1)) == article_id:
                    return d
        except Exception:
            continue
    return None

def _load_article_detail_from_dir(article_id: int):
    """从目录加载文章详情，组装成统一的数据结构。"""
    d = _find_article_dir_by_id(article_id)
    if not d:
        return None

    original_path = os.path.join(d, "original_text.json")
    sentences_path = os.path.join(d, "sentences.json")
    tokens_path = os.path.join(d, "tokens.json")

    try:
        original = _load_json_file(original_path) if os.path.exists(original_path) else {}
        sentences = _load_json_file(sentences_path) if os.path.exists(sentences_path) else []
        tokens = _load_json_file(tokens_path) if os.path.exists(tokens_path) else []

        detail = {
            "text_id": int(original.get("text_id", article_id)),
            "text_title": original.get("text_title", "Article"),
            "sentences": sentences if isinstance(sentences, list) else [],
            "total_sentences": len(sentences) if isinstance(sentences, list) else 0,
            "total_tokens": len(tokens) if isinstance(tokens, list) else 0,
        }
        return detail
    except Exception as e:
        print(f"Error loading detail from dir {d}: {e}")
        return None

def _mark_tokens_selectable(data):
    """标记token的可选择性（只有text类型可选）"""
    if 'sentences' in data:
        for sentence in data['sentences']:
            if 'tokens' in sentence:
                for token in sentence['tokens']:
                    if isinstance(token, dict) and token.get('token_type') == 'text':
                        token['selectable'] = True
                    else:
                        token['selectable'] = False
    return data

# 创建FastAPI应用
app = FastAPI(title="AI Language Learning API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件（用于调试）
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"📥 [Request] {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"📤 [Response] {request.method} {request.url.path} -> {response.status_code}")
    return response

# 注册新的标注API路由
if notation_router:
    app.include_router(notation_router)
    print("[OK] 注册新的标注API路由: /api/v2/notations")

# 注册认证API路由
try:
    from backend.api.auth_routes import router as auth_router, get_current_user
    from database_system.business_logic.models import User
    app.include_router(auth_router)
    print("[OK] 注册认证API路由: /api/auth")
except ImportError as e:
    print(f"Warning: Could not import auth_routes: {e}")
    # 如果导入失败，提供一个占位函数
    def get_current_user():
        raise HTTPException(status_code=500, detail="认证系统未加载")
    User = None

# 注册文章API路由
try:
    from backend.api.text_routes import router as text_router
    app.include_router(text_router)
    print("[OK] 注册文章API路由: /api/v2/texts")
except ImportError as e:
    print(f"Warning: Could not import text_routes: {e}")

# 注册词汇API路由
try:
    from backend.api.vocab_routes import router as vocab_router
    app.include_router(vocab_router)
    print("[OK] 注册词汇API路由: /api/v2/vocab")
except ImportError as e:
    print(f"Warning: Could not import vocab_routes: {e}")

# 注册语法API路由
try:
    from backend.api.grammar_routes import router as grammar_router
    app.include_router(grammar_router)
    print("[OK] 注册语法API路由: /api/v2/grammar")
except ImportError as e:
    print(f"Warning: Could not import grammar_routes: {e}")

@app.get("/")
async def root():
    return {"message": "AI Language Learning API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/api/debug/db-info")
async def debug_db_info():
    """调试端点：显示数据库连接信息"""
    from database_system.database_manager import DatabaseManager
    import sqlite3
    import os
    
    db_manager = DatabaseManager('development')
    engine = db_manager.get_engine()
    db_url = str(engine.url)
    
    # 提取文件路径
    db_path = db_url.replace('sqlite:///', '')
    if db_path.startswith('/') and ':' in db_path:
        db_path = db_path[1:]
    
    # 获取绝对路径
    abs_path = os.path.abspath(db_path)
    
    info = {
        "db_url": db_url,
        "db_path": db_path,
        "abs_path": abs_path,
        "cwd": os.getcwd(),
        "exists": os.path.exists(db_path),
        "tables": []
    }
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        info["tables"] = tables
        info["file_size"] = os.path.getsize(db_path)
        conn.close()
    
    return info

# ==================== Session Management API ====================
# 这些API原本在server_frontend_mock.py中，现在添加到主服务器以支持前端功能

# 初始化全局 SessionState（使用完整的 SessionState 类）
from backend.assistants.chat_info.session_state import SessionState
from backend.assistants.chat_info.selected_token import SelectedToken
from backend.data_managers.data_classes_new import Sentence as NewSentence

session_state = SessionState()
print("[OK] SessionState singleton initialized")

# 初始化全局 DataController
from backend.data_managers import data_controller

# 数据文件路径
DATA_DIR = os.path.join(BACKEND_DIR, "data", "current")
GRAMMAR_PATH = os.path.join(DATA_DIR, "grammar.json")
VOCAB_PATH = os.path.join(DATA_DIR, "vocab.json")
TEXT_PATH = os.path.join(DATA_DIR, "original_texts.json")
DIALOGUE_RECORD_PATH = os.path.join(DATA_DIR, "dialogue_record.json")
DIALOGUE_HISTORY_PATH = os.path.join(DATA_DIR, "dialogue_history.json")

global_dc = data_controller.DataController(max_turns=100)
print("✅ Global DataController created")

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

# 异步保存数据的辅助函数
def save_data_async(dc, grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path):
    """后台异步保存数据"""
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

@app.post("/api/session/set_sentence")
async def set_session_sentence(payload: dict):
    """设置当前句子上下文"""
    try:
        print(f"[Session] Setting session sentence")
        sentence_data = payload.get('sentence', payload)
        sentence = NewSentence(
            text_id=sentence_data['text_id'],
            sentence_id=sentence_data['sentence_id'],
            sentence_body=sentence_data['sentence_body'],
            tokens=tuple(sentence_data.get('tokens', []))
        )
        session_state.set_current_sentence(sentence)
        return {"success": True, "message": "Sentence context set"}
    except Exception as e:
        print(f"[Session] Error setting sentence: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/session/select_token")
async def set_session_selected_token(payload: dict):
    """设置选中的token"""
    try:
        print(f"[Session] Setting selected token")
        token_data = payload.get('token', {})
        selected_token = SelectedToken(
            token_indices=token_data.get('token_indices', [-1]),
            token_text=token_data.get('token_text', ''),
            sentence_body=session_state.current_sentence.sentence_body if session_state.current_sentence else '',
            sentence_id=session_state.current_sentence.sentence_id if session_state.current_sentence else 0,
            text_id=session_state.current_sentence.text_id if session_state.current_sentence else 0
        )
        session_state.set_current_selected_token(selected_token)
        return {"success": True, "message": "Token context set"}
    except Exception as e:
        print(f"[Session] Error setting token: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/session/update_context")
async def update_session_context(payload: dict):
    """一次性更新会话上下文（批量更新）"""
    try:
        print(f"[SessionState] 批量更新上下文...")
        updated_fields = []
        
        # 更新 current_input
        if 'current_input' in payload:
            session_state.set_current_input(payload['current_input'])
            updated_fields.append('current_input')
        
        # 更新句子
        if 'sentence' in payload:
            sentence_data = payload['sentence']
            print(f"🔍 [SessionState] 设置句子上下文:")
            print(f"  - text_id: {sentence_data.get('text_id')} (type: {type(sentence_data.get('text_id'))})")
            print(f"  - sentence_id: {sentence_data.get('sentence_id')}")
            print(f"  - sentence_body: {sentence_data.get('sentence_body', '')[:50]}...")
            
            current_sentence = NewSentence(
                text_id=sentence_data['text_id'],
                sentence_id=sentence_data['sentence_id'],
                sentence_body=sentence_data['sentence_body'],
                tokens=tuple(sentence_data.get('tokens', []))
            )
            session_state.set_current_sentence(current_sentence)
            updated_fields.append('sentence')
        
        # 更新 token
        if 'token' in payload:
            token_data = payload['token']
            
            # 🔧 如果 token_data 为 None，明确清除 token 选择
            if token_data is None:
                print("[SessionState] 清除 token 选择（token = null）")
                session_state.set_current_selected_token(None)
                updated_fields.append('token (cleared)')
            elif session_state.current_sentence:
                # token_data 不为 None，设置新的 token
                current_sentence = session_state.current_sentence
                if 'multiple_tokens' in token_data:
                    # 多个token
                    token_indices = token_data.get('token_indices', [])
                    token_text = token_data.get('token_text', '')
                    selected_token = SelectedToken(
                        token_indices=token_indices,
                        token_text=token_text,
                        sentence_body=current_sentence.sentence_body,
                        sentence_id=current_sentence.sentence_id,
                        text_id=current_sentence.text_id
                    )
                else:
                    # 单个token
                    sentence_token_id = token_data.get('sentence_token_id')
                    token_indices = [sentence_token_id] if sentence_token_id is not None else [-1]
                    selected_token = SelectedToken(
                        token_indices=token_indices,
                        token_text=token_data.get('token_body', current_sentence.sentence_body),
                        sentence_body=current_sentence.sentence_body,
                        sentence_id=current_sentence.sentence_id,
                        text_id=current_sentence.text_id
                    )
                session_state.set_current_selected_token(selected_token)
                updated_fields.append('token')
        
        return {
            'success': True,
            'message': 'Session context updated',
            'updated_fields': updated_fields
        }
    except Exception as e:
        import traceback
        print(f"[SessionState] Error updating context: {e}")
        print(f"[SessionState] Traceback:\n{traceback.format_exc()}")
        return {'success': False, 'error': str(e)}

@app.post("/api/session/reset")
async def reset_session_state(payload: dict):
    """重置会话状态"""
    try:
        print(f"[Session] Resetting session state")
        session_state.reset()
        return {"success": True, "message": "Session state reset"}
    except Exception as e:
        print(f"[Session] Error resetting session: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/admin/sync-to-db")
async def trigger_sync_to_db():
    """手动触发 JSON 数据同步到数据库"""
    try:
        print("🔄 [Admin] Manual sync triggered")
        _sync_to_database()
        return {"success": True, "message": "Data synced to database"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _sync_to_database(user_id: int = None):
    """同步 JSON 数据到数据库
    
    参数:
        user_id: 当前用户ID，用于关联新创建的数据
    """
    try:
        from database_system.database_manager import DatabaseManager
        from backend.data_managers import GrammarRuleManagerDB, VocabManagerDB
        
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        
        try:
            from backend.data_managers import OriginalTextManagerDB
            grammar_db_mgr = GrammarRuleManagerDB(session)
            vocab_db_mgr = VocabManagerDB(session)
            text_db_mgr = OriginalTextManagerDB(session)
            
            # 首先同步文章数据（必须先同步，因为grammar/vocab examples依赖于texts表）
            print("📄 [Sync] 同步文章数据...")
            synced_texts = 0
            for text_id, text_obj in global_dc.text_manager.original_texts.items():
                # 检查文章是否已存在
                existing_text = text_db_mgr.get_text_by_id(text_id, include_sentences=False)
                if not existing_text:
                    # 文章不存在，创建基本记录（句子数据通过文章上传API处理）
                    title = getattr(text_obj, 'text_title', f'Article {text_id}')
                    new_text = text_db_mgr.add_text(title, user_id=user_id)
                    print(f"✅ [Sync] 新增文章占位符: {title} (ID: {new_text.text_id})")
                    print(f"  ℹ️  句子数据需要通过文章上传API导入")
                    synced_texts += 1
                else:
                    print(f"📝 [Sync] 文章已存在: {existing_text.text_title} (ID: {text_id})")
            
            print(f"✅ [Sync] 文章同步完成: {synced_texts} 个新文章基本信息")
            
            # 同步 Grammar Rules（只同步本轮新增的）
            print(f"📚 [Sync] 同步本轮新增的 Grammar Rules (共{len(session_state.grammar_to_add)}个)...")
            synced_grammar = 0
            for grammar_item in session_state.grammar_to_add:
                rule_name = grammar_item.rule_name
                rule_explanation = grammar_item.rule_explanation
                
                # 检查是否已存在
                existing = grammar_db_mgr.get_rule_by_name(rule_name)
                if not existing:
                    # 添加新的 grammar rule
                    new_rule = grammar_db_mgr.add_new_rule(
                        name=rule_name,
                        explanation=rule_explanation or '',
                        source='auto',
                        user_id=user_id
                    )
                    print(f"✅ [Sync] 新增 grammar rule: {rule_name} (ID: {new_rule.rule_id})")
                    synced_grammar += 1
                    
                    # 同步本轮的grammar notation（如果有）
                    for notation in session_state.created_grammar_notations:
                        # 只同步与当前rule相关的notation（通过grammar_id匹配）
                        # 注意：此时新rule刚创建，需要在assistant中先记录rule_id
                        pass  # TODO: 需要从assistant中传递grammar_id映射
                else:
                    print(f"📝 [Sync] Grammar rule已存在: {rule_name}")
            
            # 同步 Vocab Expressions（只同步本轮新增的）
            print(f"📖 [Sync] 同步本轮新增的 Vocab Expressions (共{len(session_state.vocab_to_add)}个)...")
            synced_vocab = 0
            
            # 从session_state获取本轮新增的vocab
            for vocab_item in session_state.vocab_to_add:
                vocab_body = vocab_item.vocab
                
                # 在global_dc中查找对应的bundle
                bundle = None
                for vid, vb in global_dc.vocab_manager.vocab_bundles.items():
                    if getattr(vb, 'vocab_body', None) == vocab_body:
                        bundle = vb
                        break
                
                if not bundle:
                    print(f"⚠️ [Sync] 在内存中找不到vocab: {vocab_body}")
                    continue
                
                explanation = getattr(bundle, 'explanation', '')
                examples = getattr(bundle, 'examples', None) or getattr(bundle, 'example', [])
                
                # 检查是否已存在于数据库
                existing = vocab_db_mgr.get_vocab_by_body(vocab_body)
                if not existing:
                    # 添加新的 vocab
                    new_vocab = vocab_db_mgr.add_new_vocab(
                        vocab_body=vocab_body,
                        explanation=explanation,
                        user_id=user_id
                    )
                    print(f"✅ [Sync] 新增 vocab: {vocab_body} (ID: {new_vocab.vocab_id})")
                    synced_vocab += 1
                    
                    # 同步 examples
                    print(f"🔍 [Sync] Vocab {vocab_body} 有 {len(examples)} 个 examples")
                    added_examples = 0
                    skipped_examples = 0
                    for ex in examples:
                        try:
                            # 调试：打印example的完整信息
                            print(f"  🔍 [Debug] Example详情: text_id={ex.text_id}, sentence_id={ex.sentence_id}, type={type(ex.text_id)}")
                            
                            # 先检查text_id是否存在
                            from database_system.business_logic.managers import TextManager
                            text_mgr = TextManager(session)
                            if not text_mgr.get_text(ex.text_id):
                                print(f"  ⚠️ 跳过 example (text_id={ex.text_id} 不存在): sentence_id={ex.sentence_id}")
                                skipped_examples += 1
                                continue
                            
                            vocab_db_mgr.add_vocab_example(
                                vocab_id=new_vocab.vocab_id,
                                text_id=ex.text_id,
                                sentence_id=ex.sentence_id,
                                context_explanation=getattr(ex, 'context_explanation', ''),
                                token_indices=getattr(ex, 'token_indices', [])
                            )
                            print(f"  ✅ 添加 example: text_id={ex.text_id}, sentence_id={ex.sentence_id}")
                            added_examples += 1
                        except Exception as ex_err:
                            print(f"  ❌ Example 添加失败: {ex_err}")
                            skipped_examples += 1
                    
                    if skipped_examples > 0:
                        print(f"  ⚠️ {skipped_examples} 个 examples 被跳过（text_id不存在或其他错误）")
                else:
                    print(f"📝 [Sync] Vocab已存在，跳过: {vocab_body}")
            
            session.commit()
            print(f"✅ [Sync] 数据库同步完成: {synced_grammar} grammar rules, {synced_vocab} vocab expressions")
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ [Sync] 数据库同步失败: {e}")
        import traceback
        traceback.print_exc()

@app.post("/api/chat")
async def chat_with_assistant(payload: dict, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """聊天功能（完整 MainAssistant 集成）"""
    try:
        import time
        request_id = int(time.time() * 1000) % 10000
        user_id = current_user.user_id  # 获取当前用户ID
        
        # 设置session_state的user_id
        session_state.user_id = user_id
        
        print("\n" + "="*80)
        print(f"💬 [Chat #{request_id}] ========== Chat endpoint called ==========")
        print(f"📥 [Chat #{request_id}] Payload: {payload}")
        print(f"👤 [Chat #{request_id}] User ID: {user_id}")
        print("="*80)
        
        # 从 session_state 获取上下文信息
        current_sentence = session_state.current_sentence
        current_selected_token = session_state.current_selected_token
        current_input = session_state.current_input
        
        print(f"📋 [Chat #{request_id}] Session State Info:")
        print(f"  - current_input: {current_input}")
        print(f"  - current_sentence text_id: {current_sentence.text_id if current_sentence else 'None'}")
        print(f"  - current_sentence sentence_id: {current_sentence.sentence_id if current_sentence else 'None'}")
        print(f"  - current_sentence: {current_sentence.sentence_body[:50] if current_sentence else 'None'}...")
        print(f"  - current_selected_token: {current_selected_token}")
        if current_selected_token:
            print(f"    - token_text: {current_selected_token.token_text}")
            print(f"    - token_indices: {current_selected_token.token_indices if hasattr(current_selected_token, 'token_indices') else 'N/A'}")
        
        # 验证必要的参数
        if not current_sentence:
            return {
                'success': False,
                'error': 'No sentence context in session state. Please select a sentence first.'
            }
        
        if not current_input:
            current_input = payload.get('user_question', '')
            if not current_input:
                return {
                    'success': False,
                    'error': 'No user question provided'
                }
            session_state.set_current_input(current_input)
        
        # 准备 selected_text
        selected_text = None
        if current_selected_token and current_selected_token.token_text:
            if hasattr(current_selected_token, 'token_indices') and current_selected_token.token_indices == [-1]:
                selected_text = None
            elif current_selected_token.token_text.strip() == current_sentence.sentence_body.strip():
                selected_text = None
            else:
                selected_text = current_selected_token.token_text
        
        # 创建 MainAssistant 实例
        from backend.assistants.main_assistant import MainAssistant
        main_assistant = MainAssistant(
            data_controller_instance=global_dc,
            session_state_instance=session_state
        )
        
        print(f"🚀 [Chat] 调用 MainAssistant...")
        
        # 先返回主回答，其余完整流程放后台
        effective_sentence_body = selected_text if selected_text else current_sentence.sentence_body
        print("🚀 [Chat] 生成主回答...")
        ai_response = main_assistant.answer_question_function(
            quoted_sentence=current_sentence,
            user_question=current_input,
            sentence_body=effective_sentence_body
        )
        print("✅ [Chat] 主回答就绪")
        
        # 准备返回的摘要数据（从后台任务获取）
        grammar_summaries = []
        vocab_summaries = []
        grammar_to_add = []
        vocab_to_add = []
        
        # 后台执行完整流程
        def _run_full_flow_background():
            from backend.assistants import main_assistant as _ma_mod
            prev_disable_grammar = getattr(_ma_mod, 'DISABLE_GRAMMAR_FEATURES', True)
            try:
                print("\n🛠️ [Background] 启动完整流程...")
                _ma_mod.DISABLE_GRAMMAR_FEATURES = False
                main_assistant.run(
                    quoted_sentence=current_sentence,
                    user_question=current_input,
                    selected_text=selected_text
                )
                
                # 🔧 先检查内存中的 examples
                print("\n🔍 [DEBUG] 检查内存中的 vocab examples:")
                for vid, vb in list(global_dc.vocab_manager.vocab_bundles.items())[-3:]:
                    # 兼容新旧结构
                    exs = getattr(vb, 'examples', None) or getattr(vb, 'example', [])
                    vocab_body = getattr(vb, 'vocab_body', 'unknown')
                    print(f"  Vocab '{vocab_body}' (ID {vid}): {len(exs)} examples")
                    if exs:
                        for ex in exs[:2]:  # 只显示前2个
                            print(f"    - text_id={ex.text_id}, sentence_id={ex.sentence_id}")
                
                # 🔧 同步到数据库（在内存数据还在时立即同步）
                print("\n💾 [Background] 同步新数据到数据库...")
                _sync_to_database(user_id=user_id)
                
                # 保存到 JSON 文件（保持兼容）
                save_data_async(
                    dc=global_dc,
                    grammar_path=GRAMMAR_PATH,
                    vocab_path=VOCAB_PATH,
                    text_path=TEXT_PATH,
                    dialogue_record_path=DIALOGUE_RECORD_PATH,
                    dialogue_history_path=DIALOGUE_HISTORY_PATH
                )
                
                print("✅ [Background] 完整流程与保存完成")
            except Exception as bg_e:
                print(f"❌ [Background] 完整流程失败: {bg_e}")
                import traceback
                print(traceback.format_exc())
            finally:
                _ma_mod.DISABLE_GRAMMAR_FEATURES = prev_disable_grammar
        
        background_tasks.add_task(_run_full_flow_background)
        
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
        print(f"❌ [Chat] Error: {e}")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}

@app.get("/api/vocab-example-by-location")
async def get_vocab_example_by_location(
    text_id: int = Query(..., description="文章ID"),
    sentence_id: Optional[int] = Query(None, description="句子ID"),
    token_index: Optional[int] = Query(None, description="Token索引")
):
    """按位置查找词汇例句"""
    try:
        print(f"🔍 [VocabExample] Searching by location: text_id={text_id}, sentence_id={sentence_id}, token_index={token_index}")
        
        # 使用全局 DataController 查找例句
        example = global_dc.vocab_manager.get_vocab_example_by_location(text_id, sentence_id, token_index)
        
        if example:
            print(f"✅ [VocabExample] Found example")
            
            # 转换为字典格式返回
            example_dict = {
                'vocab_id': example.vocab_id,
                'text_id': example.text_id,
                'sentence_id': example.sentence_id,
                'context_explanation': example.context_explanation,
                'token_indices': getattr(example, 'token_indices', []),
                'token_index': token_index  # 添加 token_index 供前端使用
            }
            
            return {
                'success': True,
                'data': example_dict,
                'message': f'Found vocab example'
            }
        else:
            print(f"❌ [VocabExample] No example found")
            return {
                'success': False,
                'data': None,
                'message': f'No vocab example found'
            }
            
    except Exception as e:
        print(f"❌ [VocabExample] Error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

@app.get("/api/vocab", response_model=ApiResponse)
async def get_vocab_list():
    """获取词汇列表"""
    try:
        vocab_list = data_service.get_vocab_data()
        
        return create_success_response(
            data=[vocab.model_dump() for vocab in vocab_list],
            message=f"成功获取词汇列表，共 {len(vocab_list)} 条记录"
        )
        
    except Exception as e:
        return create_error_response(f"获取词汇列表失败: {str(e)}")

@app.get("/api/vocab/{vocab_id}", response_model=ApiResponse)
async def get_vocab_detail(vocab_id: int):
    """获取词汇详情"""
    try:
        vocab_list = data_service.get_vocab_data()
        vocab = next((v for v in vocab_list if v.vocab_id == vocab_id), None)
        
        if not vocab:
            return create_error_response(f"词汇不存在: {vocab_id}")
        
        return create_success_response(
            data=vocab.model_dump(),
            message=f"成功获取词汇详情: {vocab.vocab_body}"
        )
        
    except Exception as e:
        return create_error_response(f"获取词汇详情失败: {str(e)}")

@app.get("/api/grammar", response_model=ApiResponse)
async def get_grammar_list():
    """获取语法规则列表"""
    try:
        grammar_list = data_service.get_grammar_data()
        
        return create_success_response(
            data=[grammar.model_dump() for grammar in grammar_list],
            message=f"成功获取语法规则列表，共 {len(grammar_list)} 条记录"
        )
        
    except Exception as e:
        return create_error_response(f"获取语法规则列表失败: {str(e)}")

@app.get("/api/stats", response_model=ApiResponse)
async def get_stats():
    """获取数据统计信息"""
    try:
        vocab_list = data_service.get_vocab_data()
        grammar_list = data_service.get_grammar_data()
        
        stats = {
            "vocab": {
                "total": len(vocab_list),
                "starred": len([v for v in vocab_list if v.is_starred])
            },
            "grammar": {
                "total": len(grammar_list),
                "starred": len([g for g in grammar_list if g.is_starred])
            }
        }
        
        return create_success_response(
            data=stats,
            message="成功获取统计数据"
        )
        
    except Exception as e:
        return create_error_response(f"获取统计数据失败: {str(e)}")

@app.get("/api/articles", response_model=ApiResponse)
async def list_articles():
    """获取文章列表摘要（优先使用文件系统，兼容 *_processed_*.json 与 text_<id>/ 结构）"""
    try:
        summaries = _collect_articles_summary()
        return create_success_response(
            data=summaries,
            message=f"成功获取文章列表，共 {len(summaries)} 篇"
        )
    except Exception as e:
        return create_error_response(f"获取文章列表失败: {str(e)}")

@app.get("/api/v2/texts/fallback")
async def get_texts_fallback():
    """文章列表回退接口（使用文件系统数据）"""
    try:
        summaries = _collect_articles_summary()
        return {
            "success": True,
            "data": {
                "texts": summaries,
                "count": len(summaries),
                "source": "filesystem"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/articles/{article_id}", response_model=ApiResponse)
async def get_article_detail(article_id: int):
    """获取单篇文章详情，并标记 token 的可选择性（只有 text 类型可选）"""
    try:
        # 先尝试目录结构
        data = _load_article_detail_from_dir(article_id)
        if data is None:
            # 兼容历史单文件
            for path in _iter_processed_files():
                try:
                    fdata = _load_json_file(path)
                    if int(fdata.get("text_id", -1)) == article_id:
                        data = fdata
                        break
                except Exception:
                    continue

        if data is None:
            return create_error_response(f"文章不存在: {article_id}")

        data = _mark_tokens_selectable(data)

        return create_success_response(
            data=data,
            message=f"成功获取文章详情: {data.get('text_title', '')}"
        )
    except Exception as e:
        return create_error_response(f"获取文章详情失败: {str(e)}")

# 新增：文件上传处理API
@app.post("/api/upload/file", response_model=ApiResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form("Untitled Article")
):
    """上传文件并进行预处理"""
    try:
        # 读取文件内容
        content = await file.read()
        
        # 根据文件类型处理内容
        if file.filename.endswith('.txt') or file.filename.endswith('.md'):
            text_content = content.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            # TODO: 添加PDF处理
            return create_error_response("PDF处理功能暂未实现")
        else:
            return create_error_response(f"不支持的文件格式: {file.filename}")
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 开始处理文章: {title}")
            result = process_article(text_content, article_id, title)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            return create_success_response(
                data={
                    "article_id": article_id,
                    "title": title,
                    "total_sentences": result['total_sentences'],
                    "total_tokens": result['total_tokens']
                },
                message=f"文件上传并处理成功: {title}"
            )
        else:
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        return create_error_response(f"文件上传处理失败: {str(e)}")

# 新增：URL内容抓取API
@app.post("/api/upload/url", response_model=ApiResponse)
async def upload_url(
    url: str = Form(...),
    title: str = Form("URL Article")
):
    """从URL抓取内容并进行预处理"""
    try:
        # 抓取URL内容
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 简单提取文本内容（这里可以集成更复杂的HTML解析）
        text_content = response.text
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 开始处理URL文章: {title}")
            result = process_article(text_content, article_id, title)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            return create_success_response(
                data={
                    "article_id": article_id,
                    "title": title,
                    "url": url,
                    "total_sentences": result['total_sentences'],
                    "total_tokens": result['total_tokens']
                },
                message=f"URL内容抓取并处理成功: {title}"
            )
        else:
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        return create_error_response(f"URL内容抓取失败: {str(e)}")

# 新增：文字输入处理API
@app.post("/api/upload/text", response_model=ApiResponse)
async def upload_text(
    text: str = Form(...),
    title: str = Form("Text Article")
):
    """直接处理文字内容"""
    try:
        if not text.strip():
            return create_error_response("文字内容不能为空")
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 开始处理文字内容: {title}")
            result = process_article(text, article_id, title)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            return create_success_response(
                data={
                    "article_id": article_id,
                    "title": title,
                    "total_sentences": result['total_sentences'],
                    "total_tokens": result['total_tokens']
                },
                message=f"文字内容处理成功: {title}"
            )
        else:
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        return create_error_response(f"文字内容处理失败: {str(e)}")

# ==================== Asked Tokens API ====================

@app.get("/api/user/asked-tokens")
async def get_asked_tokens(user_id: str = Query(..., description="用户ID"), 
                          text_id: int = Query(..., description="文章ID"),
                          include_new_system: bool = Query(False, description="是否包含新系统数据")):
    """
    获取用户在指定文章下已提问的 token 键集合
    
    支持两种模式：
    1. 传统模式（include_new_system=False）：只返回旧系统数据
    2. 兼容模式（include_new_system=True）：合并新旧系统数据
    """
    try:
        print(f"[AskedTokens] Getting asked tokens for user={user_id}, text_id={text_id}, include_new_system={include_new_system}")
        
        # 使用 JSON 文件模式（测试阶段）
        manager = get_asked_tokens_manager(use_database=False)
        asked_tokens = manager.get_asked_tokens_for_article(user_id, text_id)
        
        result_data = {
            "asked_tokens": list(asked_tokens),
            "count": len(asked_tokens),
            "source": "legacy_system"
        }
        
        # 如果请求包含新系统数据，合并结果
        if include_new_system:
            try:
                from data_managers.unified_notation_manager import get_unified_notation_manager
                unified_manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=False)
                
                # 获取新系统的所有标注
                new_notations = unified_manager.get_notations("all", text_id, user_id)
                
                # 合并数据（去重）
                all_notations = set(asked_tokens)
                all_notations.update(new_notations)
                
                result_data.update({
                    "asked_tokens": list(all_notations),
                    "count": len(all_notations),
                    "legacy_count": len(asked_tokens),
                    "new_system_count": len(new_notations),
                    "source": "merged_systems"
                })
                
                print(f"[AskedTokens] Merged data: {len(asked_tokens)} legacy + {len(new_notations)} new = {len(all_notations)} total")
                
            except Exception as e:
                print(f"[WARN] Failed to get new system data: {e}")
                # 继续使用旧系统数据
        
        print(f"[AskedTokens] Found {result_data['count']} total tokens")
        return create_success_response(
            data=result_data,
            message=f"成功获取已提问的 tokens，共 {result_data['count']} 个"
        )
    except Exception as e:
        print(f"[AskedTokens] Error getting asked tokens: {e}")
        return create_error_response(f"获取已提问 tokens 失败: {str(e)}")

@app.post("/api/user/asked-tokens")
async def mark_token_asked(payload: dict):
    """
    标记 token 或 sentence 为已提问
    
    支持两种类型的标记：
    1. type='token': 标记单词（需要 sentence_token_id）
    2. type='sentence': 标记句子（sentence_token_id 可选）
    
    向后兼容：如果 type 未指定但 sentence_token_id 存在，默认为 'token'
    新系统集成：同时创建 VocabNotation 或 GrammarNotation
    """
    try:
        user_id = payload.get("user_id", "default_user")  # 默认用户ID
        text_id = payload.get("text_id")
        sentence_id = payload.get("sentence_id")
        sentence_token_id = payload.get("sentence_token_id")
        type_param = payload.get("type", None)  # 新增：标记类型
        vocab_id = payload.get("vocab_id", None)  # 新增：词汇ID
        grammar_id = payload.get("grammar_id", None)  # 新增：语法ID
        
        # 向后兼容逻辑：如果 type 未指定但 sentence_token_id 不为空，默认为 'token'
        if type_param is None:
            if sentence_token_id is not None:
                type_param = "token"
            else:
                type_param = "sentence"
        
        print(f"[AskedTokens] Marking as asked:")
        print(f"  - user_id: {user_id}")
        print(f"  - text_id: {text_id}")
        print(f"  - sentence_id: {sentence_id}")
        print(f"  - sentence_token_id: {sentence_token_id}")
        print(f"  - type: {type_param}")
        print(f"  - vocab_id: {vocab_id}")
        print(f"  - grammar_id: {grammar_id}")
        
        # 验证必需参数
        if not text_id or sentence_id is None:
            return create_error_response("text_id 和 sentence_id 是必需的")
        
        # 如果是 token 类型，sentence_token_id 必须提供
        if type_param == "token" and sentence_token_id is None:
            return create_error_response("type='token' 时，sentence_token_id 是必需的")
        
        # 使用旧系统（向后兼容）
        manager = get_asked_tokens_manager(use_database=False)
        success = manager.mark_token_asked(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_token_id=sentence_token_id,
            type=type_param,
            vocab_id=vocab_id,
            grammar_id=grammar_id
        )
        
        # 同时使用新系统（向前兼容）
        if success:
            try:
                from data_managers.unified_notation_manager import get_unified_notation_manager
                unified_manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=False)
                
                if type_param == "token":
                    # 创建词汇标注
                    unified_manager.mark_notation(
                        notation_type="vocab",
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        token_id=sentence_token_id,
                        vocab_id=vocab_id
                    )
                elif type_param == "sentence":
                    # 创建语法标注
                    unified_manager.mark_notation(
                        notation_type="grammar",
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        grammar_id=grammar_id,
                        marked_token_ids=[]
                    )
                print(f"[AskedTokens] Also created new system notation")
            except Exception as e:
                print(f"[WARN] Failed to create new system notation: {e}")
                # 不阻止旧系统操作成功
        
        if success:
            print(f" [AskedTokens] Token marked as asked successfully")
            return create_success_response(
                data={
                    "user_id": user_id,
                    "text_id": text_id,
                    "sentence_id": sentence_id,
                    "sentence_token_id": sentence_token_id
                },
                message="Token 已标记为已提问"
            )
        else:
            return create_error_response("标记 token 为已提问失败")
    except Exception as e:
        print(f" [AskedTokens] Error marking token as asked: {e}")
        return create_error_response(f"标记 token 为已提问失败: {str(e)}")

@app.delete("/api/user/asked-tokens")
async def unmark_token_asked(payload: dict):
    """取消标记 token 为已提问"""
    try:
        user_id = payload.get("user_id", "default_user")  # 默认用户ID
        token_key = payload.get("token_key")
        
        print(f" [AskedTokens] Unmarking token: user={user_id}, key={token_key}")
        
        if not token_key:
            return create_error_response("token_key 是必需的")
        
        # 使用 JSON 文件模式（测试阶段）
        manager = get_asked_tokens_manager(use_database=False)
        success = manager.unmark_token_asked(user_id, token_key)
        
        if success:
            print(f" [AskedTokens] Token unmarked successfully")
            return create_success_response(
                data={"token_key": token_key},
                message="Token 已取消标记"
            )
        else:
            return create_error_response("取消标记 token 失败")
    except Exception as e:
        print(f" [AskedTokens] Error unmarking token: {e}")
        return create_error_response(f"取消标记 token 失败: {str(e)}")

# ==================== End Asked Tokens API ====================

if __name__ == "__main__":
    import uvicorn
    
    # 打印所有注册的路由（调试用）
    print("\n" + "="*80)
    print("📋 已注册的API路由：")
    print("="*80)
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'N/A'
            print(f"  {methods:8} {route.path}")
    print("="*80 + "\n")
    
    print("="*80)
    print("🚀 启动数据库后端服务器（含 Chat/Session/MainAssistant）")
    print("="*80)
    print("📡 端口: 8000")
    print("📊 功能:")
    print("  ✅ Session 管理")
    print("  ✅ Chat 聊天（MainAssistant）")
    print("  ✅ Vocab/Grammar CRUD")
    print("  ✅ Notation 管理（主 ORM）")
    print("  ✅ Articles 上传与查看")
    print("="*80 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
